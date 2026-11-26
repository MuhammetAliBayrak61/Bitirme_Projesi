process.env.VITE_OFFLINE='true';
const {build}=await import('vite');
await build();
