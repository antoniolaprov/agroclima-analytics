import "@testing-library/jest-dom/vitest";

// Recharts usa ResizeObserver e mede o container; em jsdom ambos precisam de ajuda.
class ResizeObserverFalso {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = globalThis.ResizeObserver ?? (ResizeObserverFalso as never);

Object.defineProperty(HTMLElement.prototype, "clientWidth", { configurable: true, value: 800 });
Object.defineProperty(HTMLElement.prototype, "clientHeight", { configurable: true, value: 400 });

// O ResponsiveContainer do Recharts mede o container via getBoundingClientRect,
// que o jsdom sempre retorna zerado; sem isso nenhum grafico desenha. Apenas o
// div do proprio ResponsiveContainer recebe tamanho falso: o span interno de
// medicao de texto do Recharts precisa continuar zerado, senao os eixos ficam
// com tamanho absurdo e a area do grafico colapsa.
const getBoundingClientRectOriginal = HTMLElement.prototype.getBoundingClientRect;
HTMLElement.prototype.getBoundingClientRect = function getBoundingClientRectFalso() {
  if (this.classList.contains("recharts-responsive-container")) {
    return {
      width: 800,
      height: 400,
      top: 0,
      left: 0,
      right: 800,
      bottom: 400,
      x: 0,
      y: 0,
      toJSON() {},
    };
  }
  return getBoundingClientRectOriginal.call(this);
};
