import { build } from 'esbuild';
import { mkdir, rm, copyFile, readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const output = path.join(root, 'backend/web');
await rm(output, { recursive: true, force: true });
await mkdir(path.join(output, 'assets'), { recursive: true });
await build({
  entryPoints: [path.join(root, 'web/main.tsx')],
  outfile: path.join(output, 'assets/website.js'),
  bundle: true,
  minify: true,
  jsx: 'automatic',
  nodePaths: [path.join(root, 'web/node_modules')],
  target: ['es2020'],
  logLevel: 'info',
});
await copyFile(path.join(root, 'web/index.html'), path.join(output, 'index.html'));
for (const name of await readdir(path.join(root, 'web/public'))) {
  if (/\.(png|svg)$/i.test(name)) {
    await copyFile(path.join(root, 'web/public', name), path.join(output, 'assets', name));
  }
}
console.log('Website built in backend/web');
