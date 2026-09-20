import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {T, PAPEL, fmtN, fmtR} from './tokens';
import {Marca} from './Marca';

// Cartão de prova — o número medido na base do depoente, ao lado da fala dele.
// A fala dá a emoção, o número dá a prova: é o par que nenhum concorrente consegue
// forjar, porque sai do Postgres. Os dados vêm de `dados.json`, gerado pelo
// `gerar_dados.py` (leitura pura do banco), nunca digitados à mão.

const Numero = ({valor, rotulo, sufixo = '', atraso, moeda = false}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const entrada = spring({frame: frame - atraso, fps, config: {damping: 200, mass: 0.6}});
  // A contagem termina antes da entrada para o número não ficar "girando" parado.
  const conta = interpolate(frame, [atraso, atraso + 28], [0, valor], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  return (
    <div
      style={{
        opacity: entrada,
        transform: `translateY(${(1 - entrada) * 18}px)`,
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
      }}
    >
      <div style={{...PAPEL.valor, fontFamily: T.sans, fontSize: 68, lineHeight: 1, fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap'}}>
        {moeda ? fmtR(conta) : fmtN(conta)}
        {sufixo ? <span style={{color: T.inkSoft, fontSize: 40, fontWeight: 700}}>{sufixo}</span> : null}
      </div>
      <div style={{...PAPEL.label, fontFamily: T.sans, fontSize: 19}}>{rotulo}</div>
    </div>
  );
};

export const CartaoProva = ({dados}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const marca = spring({frame, fps, config: {damping: 200}});
  const nome = spring({frame: frame - 8, fps, config: {damping: 200}});
  const faixa = spring({frame: frame - 96, fps, config: {damping: 200}});
  // Sai junto com a composição, para o corte no editor não precisar de fade manual.
  const saida = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: T.bg, fontFamily: T.sans, opacity: saida}}>
      {/* Brilho de acento no canto: a única licença decorativa, e vem do token. */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(760px 460px at 84% 10%, rgba(46,139,255,0.13), transparent 70%)`,
        }}
      />

      <AbsoluteFill style={{padding: 96, justifyContent: 'space-between'}}>
        <div style={{opacity: marca, transform: `translateY(${(1 - marca) * -14}px)`}}>
          <Marca altura={54} />
        </div>

        <div style={{opacity: nome, transform: `translateY(${(1 - nome) * 20}px)`}}>
          <div style={{...PAPEL.label, fontSize: 20, marginBottom: 16}}>Medido na base, em {dados.medido_em}</div>
          <div style={{...PAPEL.identidade, fontSize: 92, lineHeight: 1, letterSpacing: '-0.02em'}}>
            {dados.nome}
          </div>
          <div style={{color: T.inkSoft, fontSize: 28, fontWeight: 600, marginTop: 14}}>
            {dados.desde}
          </div>
        </div>

        {/* Largura travada: com 1fr em tela cheia cada número fica sozinho no meio de
            uma coluna de 576px, e a grade lê como buraco em vez de grade. O vazio que
            sobra à direita é respiro, e é onde o brilho de acento trabalha. */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '340px 340px 520px',
            rowGap: 48,
            columnGap: 24,
          }}
        >
          <Numero valor={dados.apostas} rotulo="apostas planilhadas" atraso={26} />
          {/* Em quem usa há pouco tempo, "total" e "nos últimos 30 dias" são o MESMO
              número, e repetir um número é pior que mostrar um a menos: lê como erro.
              Ali o que prova é há quantos dias ele captura. */}
          {dados.apostas_30d === dados.apostas ? (
            <Numero valor={dados.dias_90} rotulo="dias com captura" atraso={32} />
          ) : (
            <Numero valor={dados.apostas_30d} rotulo="nos últimos 30 dias" atraso={32} />
          )}
          <Numero valor={dados.turnover} rotulo="movimentados" atraso={38} moeda />
          <Numero valor={dados.casas} rotulo="casas" atraso={44} />
          <Numero valor={dados.contas} rotulo="contas" atraso={50} />
          <Numero valor={dados.tipsters} rotulo="tipsters" atraso={56} />
        </div>

        <div
          style={{
            opacity: faixa,
            transform: `translateY(${(1 - faixa) * 16}px)`,
            borderTop: `1px solid ${T.surface2}`,
            paddingTop: 34,
            display: 'flex',
            alignItems: 'baseline',
            gap: 22,
          }}
        >
          <span style={{color: T.inkSoft, fontSize: 34, fontWeight: 600}}>{dados.antes}</span>
          <span style={{color: T.accent, fontSize: 34, fontWeight: 800}}>{dados.depois}</span>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
