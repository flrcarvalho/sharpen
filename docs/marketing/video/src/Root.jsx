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

// Uma composição por depoente, derivada do JSON. Depoente novo entra no `gerar_dados.py`
// e aparece aqui sozinho: lista escrita à mão é lista que alguém esquece de atualizar.
const idDe = (chave) => 'Cartao-' + chave.charAt(0).toUpperCase() + chave.slice(1);

export const RemotionRoot = () => {
  return (
    <>
      <style>{fontes}</style>
      {Object.entries(dados).map(([chave, d]) => (
        <Composition
          key={chave}
          id={idDe(chave)}
          component={CartaoProva}
          durationInFrames={240}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{dados: d}}
        />
      ))}
    </>
  );
};
