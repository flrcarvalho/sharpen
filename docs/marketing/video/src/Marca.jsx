import React from 'react';
import {T} from './tokens';

// A marca do Sharpen, copiada do `app/static/app.html` (bloco `.brand`): a lâmina em
// gradiente azul mais a sombra cinza, e o wordmark com o ponto final depois do "en".
// Copiado de propósito, e não redesenhado: peça de marketing que reinventa o símbolo
// deixa de ser a mesma marca que está na tela do produto.
export const Marca = ({altura = 64, comWordmark = true, opacidade = 1}) => (
  <div style={{display: 'flex', alignItems: 'center', gap: altura * 0.22, opacity: opacidade}}>
    <svg viewBox="40 10 40 100" height={altura} role="img" aria-label="Sharpen">
      <defs>
        <linearGradient id="blade" x1="60" y1="16" x2="60" y2="104" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#5BA9FF" />
          <stop offset="1" stopColor="#1E7CF0" />
        </linearGradient>
      </defs>
      <path d="M60 16 L60 90 L42 104 Z" fill="url(#blade)" />
      <path d="M60 16 L78 104 L60 90 Z" fill="#333B45" />
    </svg>
    {comWordmark && (
      <div
        style={{
          fontFamily: T.sans,
          fontSize: altura * 0.62,
          fontWeight: 800,
          letterSpacing: '-0.02em',
          color: T.ink,
        }}
      >
        Sharp<span style={{color: T.accent}}>en.</span>
      </div>
    )}
  </div>
);
