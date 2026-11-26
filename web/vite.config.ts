import {defineConfig} from 'vite';
import {viteSingleFile} from 'vite-plugin-singlefile';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
export default defineConfig(() => {
 const offline=process.env.VITE_OFFLINE==='true';
 const snapshot=resolve(process.env.LST_SNAPSHOT||'src/snapshot.json');
 return {plugins:[...(offline?[viteSingleFile()]:[]),{
  name:'atlas-data',enforce:'pre',resolveId(id){if(id==='./snapshot.json'||id.endsWith('/snapshot.json'))return '\0atlas-data.js'},
  load(id){if(id!=='\0atlas-data.js')return;const data=JSON.parse(readFileSync(snapshot,'utf8'));return 'export default '+JSON.stringify(offline?data:{features:[],regions:{}})}
 }],define:{'import.meta.env.VITE_OFFLINE':JSON.stringify(offline?'true':'false')},
 server:{proxy:{'/api':'http://localhost:5274','/health':'http://localhost:5274'}}};
});
