import '@testing-library/jest-dom/vitest';
import * as zlib from 'node:zlib';

// Node / undici decompress compatibility shim
if (typeof (zlib as any).createZstdDecompress === 'undefined') {
  (zlib as any).createZstdDecompress = () => ({
    on: () => {},
    once: () => {},
    emit: () => {},
    end: () => {},
    write: () => {},
  });
}
