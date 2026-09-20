// Tokens da marca — ESPELHO de `pack/tokens/tokens.css` (tema escuro, que é o único
// tema do produto). A fonte de verdade continua sendo o CSS: mudou lá, muda aqui.
// Cor literal em componente é proibida no projeto; use sempre uma chave deste objeto.

export const T = {
  bg: '#0A0D12',
  surface: '#12161D',
  surface2: '#161B22',
  ink: '#EEF2F7',
  inkSoft: '#95A1B0',
  inkMute: '#5E6775',
  accent: '#2E8BFF',
  accent2: '#7FB2FF',
  pos: '#2BC07E',
  neg: '#E5524B',
  warn: '#E0A21A',
  sans: 'Manrope, system-ui, sans-serif',
  mono: '"JetBrains Mono", ui-monospace, monospace',
};

// Escada de Tinta: o papel do texto decide a cor, e há piso de corpo por papel.
// Em vídeo tudo é grande, então o piso nunca aperta — mas o PAPEL continua valendo:
// identidade e valor numérico em `ink`, label em `inkSoft`, e nada de `inkMute`
// carregando informação.
export const PAPEL = {
  valor: { color: T.ink, fontWeight: 800 },
  identidade: { color: T.ink, fontWeight: 700 },
  label: { color: T.inkSoft, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' },
  meta: { color: T.inkMute, fontWeight: 500 },
};

// Dinheiro no padrão do produto (`UI_REFERENCE §5`): agregado é INTEIRO e milhar com
// ponto. Nunca abreviar com k/M — é barrado pelo check-tokens no app, e a peça de
// marketing não pode contradizer a tela.
export const fmtR = (n) =>
  'R$ ' + Math.round(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 });

export const fmtN = (n) => Math.round(n).toLocaleString('pt-BR');
