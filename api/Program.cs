using Npgsql;
using System.Diagnostics;
using System.Text.Json;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.AspNetCore.ResponseCompression;
using System.Threading.RateLimiting;

var builder = WebApplication.CreateBuilder(args);
var connection = builder.Configuration.GetConnectionString("Lst") ?? throw new InvalidOperationException("ConnectionStrings__Lst gerekli.");
var cs = new NpgsqlConnectionStringBuilder(connection) { Timeout = 3, CommandTimeout = 10, IncludeErrorDetail = false };
builder.Services.AddSingleton(NpgsqlDataSource.Create(cs.ConnectionString));
builder.Services.AddProblemDetails();
builder.Services.Configure<RouteHandlerOptions>(o => o.ThrowOnBadRequest = true);
builder.Services.AddResponseCompression(o => { o.EnableForHttps = true; o.MimeTypes = ResponseCompressionDefaults.MimeTypes.Concat(["application/json"]); });
builder.Services.AddRateLimiter(options => {
    options.RejectionStatusCode = 429;
    options.AddPolicy("read", ctx => RateLimitPartition.GetFixedWindowLimiter(ctx.Connection.RemoteIpAddress?.ToString() ?? "local",
        _ => new FixedWindowRateLimiterOptions { PermitLimit = 180, Window = TimeSpan.FromMinutes(1), QueueLimit = 0 }));
});
var app = builder.Build();
app.UseResponseCompression();
app.Use(async (ctx, next) => {
    var timer = Stopwatch.StartNew();
    try { await next(); }
    catch (Exception e) when (e is NpgsqlException or TimeoutException) {
        if (!ctx.Response.HasStarted) {
            ctx.Response.Clear();
            await Results.Problem(statusCode:503, title:"Veri hizmetine ulaşılamıyor", detail:"Lütfen daha sonra yeniden deneyin.").ExecuteAsync(ctx);
        }
        app.Logger.LogWarning("Database request failed: {ErrorType}", e.GetType().Name);
    }
    catch (BadHttpRequestException) {
        if (!ctx.Response.HasStarted) { ctx.Response.Clear(); await Results.Problem(statusCode:400,title:"Geçersiz istek").ExecuteAsync(ctx); }
    }
    finally { app.Logger.LogInformation("{Method} {Path} {Status} {ElapsedMs}ms", ctx.Request.Method, ctx.Request.Path, ctx.Response.StatusCode, timer.ElapsedMilliseconds); }
});
app.UseRateLimiter();
app.UseDefaultFiles();
app.UseStaticFiles();
app.MapGet("/health/live", () => Results.Ok(new { status="alive" }));
app.MapGet("/health", async (NpgsqlDataSource db, CancellationToken stop) => {
    await using var cmd=db.CreateCommand("SELECT release_id FROM lst_active_release WHERE singleton=true");
    var id=await cmd.ExecuteScalarAsync(stop);
    return id is string ? Results.Ok(new { status="ready", release_id=id }) : Results.Problem(statusCode:503,title:"Etkin yayın bulunamadı");
});
var api = app.MapGroup("/api").RequireRateLimiting("read");
// Every response selects one release in one SQL statement; no mutable latest-row joins.
const string active = " FROM lst_release_province p JOIN lst_active_release a ON a.release_id=p.release_id ";
api.MapGet("/atlas", async (HttpContext ctx, NpgsqlDataSource db, CancellationToken stop) => {
    const string query="""
        SELECT jsonb_build_object('release',r.metadata,'regions','{}'::jsonb,'features',
        (SELECT jsonb_agg(jsonb_build_object('type','Feature','properties',jsonb_build_object('name',p.name),'geometry',ST_AsGeoJSON(p.geom)::jsonb) ORDER BY p.name)
        FROM lst_release_province p WHERE p.release_id=r.id))::text
        FROM lst_active_release a JOIN lst_release r ON a.release_id=r.id
        """;
    await using var cmd=db.CreateCommand(query);
    var value=await cmd.ExecuteScalarAsync(stop) as string;
    return value is null ? Results.Problem(statusCode:503,title:"Etkin yayın bulunamadı") : Results.Text(value,"application/json");
});
api.MapGet("/iller", async (NpgsqlDataSource db, CancellationToken stop) => {
    await using var cmd=db.CreateCommand("SELECT p.name"+active+"ORDER BY p.name");
    await using var rows=await cmd.ExecuteReaderAsync(stop);
    var names=new List<string>(); while(await rows.ReadAsync(stop))names.Add(rows.GetString(0));
    return Results.Ok(names);
});
api.MapGet("/iller/{name}", async (string name, string? release, HttpContext ctx, NpgsqlDataSource db, CancellationToken stop) => {
    if (name.Length>80) return Results.Problem(statusCode:400,title:"Geçersiz il adı");
    await using var cmd=db.CreateCommand("SELECT p.result::text,p.release_id"+active+"WHERE p.name=$1 AND ($2::text IS NULL OR p.release_id=$2)");
    cmd.Parameters.AddWithValue(name); cmd.Parameters.AddWithValue(NpgsqlTypes.NpgsqlDbType.Text,(object?)release??DBNull.Value);
    await using var rows=await cmd.ExecuteReaderAsync(stop);
    if (!await rows.ReadAsync(stop)) return Results.Problem(statusCode:release is null?404:409,title:release is null?"İl bulunamadı":"Yayın değişti; sayfayı yenileyin");
    ctx.Response.Headers["X-LST-Release"]=rows.GetString(1);
    return Results.Text(rows.GetString(0),"application/json");
});
api.MapGet("/konum", async (double? lon, double? lat, NpgsqlDataSource db, CancellationToken stop) => {
    if(lon is null||lat is null||!double.IsFinite(lon.Value)||!double.IsFinite(lat.Value)||Math.Abs(lat.Value)>90||Math.Abs(lon.Value)>180)
        return Results.Problem(statusCode:400,title:"Geçersiz koordinat",detail:"lon -180..180, lat -90..90 olmalı.");
    await using var cmd=db.CreateCommand("SELECT p.name"+active+"WHERE ST_Covers(p.geom,ST_SetSRID(ST_MakePoint($1,$2),4326)) ORDER BY p.name LIMIT 1");
    cmd.Parameters.AddWithValue(lon.Value);cmd.Parameters.AddWithValue(lat.Value);
    return await cmd.ExecuteScalarAsync(stop) is string city?Results.Ok(city):Results.Problem(statusCode:404,title:"Konum kapsam dışında");
});
api.MapGet("/tahmin-katmani", async (string? release, HttpContext ctx, NpgsqlDataSource db, CancellationToken stop) => {
    const string query="""
        SELECT a.release_id,(SELECT COALESCE(jsonb_agg(run ORDER BY p.name),'[]'::jsonb)::text
        FROM lst_release_province p CROSS JOIN LATERAL jsonb_array_elements(p.result->'runs') AS item(run)
        WHERE p.release_id=a.release_id AND run->>'mode'='province' AND run->>'publishable'='true')
        FROM lst_active_release a WHERE ($1::text IS NULL OR a.release_id=$1)
        """;
    await using var cmd=db.CreateCommand(query);cmd.Parameters.AddWithValue(NpgsqlTypes.NpgsqlDbType.Text,(object?)release??DBNull.Value);
    await using var rows=await cmd.ExecuteReaderAsync(stop);
    if(!await rows.ReadAsync(stop))return Results.Problem(statusCode:409,title:"Yayın değişti veya etkin yayın yok");
    ctx.Response.Headers["X-LST-Release"]=rows.GetString(0);
    return Results.Text(rows.GetString(1),"application/json");
});
app.Run();
public partial class Program { }
