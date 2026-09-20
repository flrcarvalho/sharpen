import React from 'react';
import {Composition, staticFile} from 'remotion';
import {CartaoProva} from './CartaoProva';
import dados from './dados.json';

// Fontes self-host, as mesmas do app (`app/static/fonts/`). Carregar por @font-face e
// não por CDN: o render tem que ser reprodutível offline, e a peça precisa sair na
// mesma tipografia da tela do produto.
const fontes = `
@font-face {
  font-family: 'Manrope';
  src: url('${staticFile('fonts/manrope-latin.woff2')}') format('woff2');
  font-weight: 200 800;
  font-display: block;
}
@font-face {
  font-family: 'JetBrains Mono';
  src: url('${staticFile('fonts/jetbrainsmono-latin.woff2')}') format('woff2');
  font-weight: 100 800;
  font-display: block;
}`;

export const RemotionRoot = () => {
  return (
    <>
      <style>{fontes}</style>
      <Composition
        id="CartaoProva"
        component={CartaoProva}
        durationInFrames={240}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{dados: dados.jonathan}}
      />
    </>
  );
};
