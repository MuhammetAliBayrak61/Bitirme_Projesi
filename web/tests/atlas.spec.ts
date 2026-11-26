import {test,expect} from '@playwright/test';
test('API mode loads only one province and presents release, scope and legend',async({page})=>{
 const start=Date.now();await page.goto('/');
 await expect(page.getByLabel('İl seçimi')).toBeVisible();
 await expect(page.getByRole('heading',{name:'Antalya · İl ortalaması',exact:true})).toBeVisible();
 await expect(page.getByLabel('Sıcaklık renk ölçeği').first()).toBeVisible();
 await expect(page.locator('header')).toContainText('LST, meteorolojik hava sıcaklığından farklıdır.');
 await expect(page.getByRole('button',{name:/İstanbul/}).first()).toBeVisible();
 await page.getByRole('button',{name:/İstanbul/}).first().focus();await page.keyboard.press('Enter');
 await expect(page.getByRole('heading',{name:'İstanbul · İl ortalaması',exact:true})).toBeVisible();
 console.log(JSON.stringify({scenario:'first_load_and_keyboard_switch',elapsed_ms:Date.now()-start}));
});
test('new province year remains distinct from the point series year',async({page})=>{
 await page.route('**/api/iller/Antalya?*',async route=>{
  const r=await route.fetch();const data=await r.json();
  // Explicit synthetic future-year fixture; no research data is changed.
  const observation={lst:21,valid_fraction:1,valid_pixels:10,total_pixels:10,complete_tiles:true};
  data.provinceHistory=[{...observation,date:'2026-01-01'},{...observation,date:'2027-01-01'}];
  data.history=[{date:'2025-01-01',lst:20}];
  await route.fulfill({json:data});
 });
 await page.goto('/');await expect(page.getByLabel('İl serisi yılı')).toHaveValue('2027');
 await expect(page.getByLabel('Tek piksel serisi yılı')).toHaveValue('2025');
});
test('API failure shows an actionable error, without stale province results',async({page})=>{
 await page.route('**/api/iller/*',route=>route.fulfill({status:503,json:{title:'unavailable'}}));
 await page.goto('/');await expect(page.getByRole('alert')).toContainText('İl verisi yüklenemedi');
 await expect(page.getByRole('button',{name:'Yeniden dene'})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Antalya · İl ortalaması',exact:true})).toHaveCount(0);
});
test('mobile retains province selection and the temperature legend',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');
 await expect(page.getByLabel('İl seçimi')).toBeVisible();await expect(page.getByLabel('Sıcaklık renk ölçeği').first()).toBeVisible();
 await page.getByLabel('İl seçimi').selectOption('Erzurum');
 await expect(page.getByRole('heading',{name:'Erzurum · İl ortalaması',exact:true})).toBeVisible();
});

test('archive toggle keeps historical forecasts separate',async({page})=>{
 await page.goto('/');await expect(page.getByRole('heading',{name:'Antalya · İl ortalaması',exact:true})).toBeVisible();
 await expect(page.locator('.cards article')).toHaveCount(2);
 await page.getByLabel('İlk eğitim arşivi').check();
 await expect(page.locator('.cards article')).toHaveCount(3);
 if(process.env.LST_VISUAL_DIR)await page.screenshot({path:process.env.LST_VISUAL_DIR+'/atlas-desktop.png',fullPage:true});
});
