import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/teste/setup.ts"],
    // Os testes de pagina montam a pagina inteira, com quatro graficos do
    // Recharts, e no jsdom isso passa de cinco segundos quando os arquivos
    // rodam em paralelo disputando a maquina. O padrao do vitest deixava a
    // suite vermelha de forma intermitente.
    testTimeout: 20000,
  },
  resolve: { alias: { "@": path.resolve(__dirname, ".") } },
});
