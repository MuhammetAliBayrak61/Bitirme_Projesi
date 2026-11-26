using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.Configuration;
using Xunit;
using System.Net;
using System.Text.Json;

public class ContractTests : IClassFixture<WebApplicationFactory<Program>>
{
    readonly HttpClient client;
    public ContractTests(WebApplicationFactory<Program> app) {
        Environment.SetEnvironmentVariable("ConnectionStrings__Lst","Host=127.0.0.1;Port=1;Username=unavailable;Database=unavailable;Timeout=1");
        client=app.WithWebHostBuilder(builder=>builder.ConfigureAppConfiguration((_,config)=>config.AddInMemoryCollection(
            new Dictionary<string,string?> { ["ConnectionStrings:Lst"]="Host=127.0.0.1;Port=1;Username=unavailable;Database=unavailable;Timeout=1" }))).CreateClient();
    }
    [Fact] public async Task LivenessDoesNotRequireDatabase() {
        var r=await client.GetAsync("/health/live"); Assert.Equal(HttpStatusCode.OK,r.StatusCode);
    }
    [Fact] public async Task MissingDatabaseReturnsControlledProblem() {
        var r=await client.GetAsync("/health"); Assert.Equal(HttpStatusCode.ServiceUnavailable,r.StatusCode);
        Assert.Equal("application/problem+json",r.Content.Headers.ContentType?.MediaType);
        var json=JsonDocument.Parse(await r.Content.ReadAsStringAsync());Assert.Equal(503,json.RootElement.GetProperty("status").GetInt32());
    }
    [Theory] [InlineData("/api/konum?lat=91&lon=30")] [InlineData("/api/konum?lat=20&lon=181")] [InlineData("/api/konum")] [InlineData("/api/konum?lat=abc&lon=30")]
    public async Task InvalidCoordinatesAreRejectedBeforeDatabase(string path) {
        var r=await client.GetAsync(path);Assert.Equal(HttpStatusCode.BadRequest,r.StatusCode);
        Assert.Equal("application/problem+json",r.Content.Headers.ContentType?.MediaType);
    }
}
