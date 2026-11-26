import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'tests',use:{baseURL:process.env.LST_TEST_URL||'http://127.0.0.1:5274'},reporter:[['list'],['json',{outputFile:'../results/verification/web-tests.json'}]]});
