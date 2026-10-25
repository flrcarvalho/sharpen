// Mundo MAIN (Stake.com — a Stake INTERNACIONAL, plataforma própria GraphQL): lê as apostas que
// a página pede e BUSCA a lista inteira ela mesma, repassando ao content script.
//
//   POST /_api/v1/graphql   { query, variables }   header `x-access-token: <sessão>`
//     SportSportList   → data.user.sportBetList[]  { id, iid, bet: SportBet | SwishBet | RacingBet | SportsbookXMultiBet }
//     ActiveBets_User  → data.user.activeSportBets[] · activeSwishBetList[] · activeRacingBets[] ·
//                        activeSportsbookXMultiBetList[]
//
// ⚠ NÃO É A STAKE QUE JÁ TÍNHAMOS. `stake.bet.br` (`stk_inject.js`) é Kambi atrás de REST próprio;
// `stake.com` é o GraphQL da casa (Cosmo Router), com outro id, outra moeda (cripto) e outro
// histórico. Casas diferentes no sistema: `Stake` e `Stake.com`.
//
// RECON s428 (25/10/2026, conta do Feca, USDT). O que foi MEDIDO:
//   • AUTH: `x-access-token` = o cookie `session` (96 caracteres, não é HttpOnly). O inject aprende o
//     header de qualquer chamada `/_api/v1/graphql` da página e, sem ela, parte do cookie a frio.
//   • A TELA CERTA é `/pt/my-bets/sports` (abas Ativo e Definido). A `/pt/sports/my-bets` do
//     sportsbook diz "Nenhum resultado" com a conta cheia de aposta.
//   • `limit` acima de 50 devolve a lista VAZIA, SEM ERRO (51, 100 e 500 medidos). O replay pede o
//     que a página pede: 20 no histórico, 50 nas abertas. Não há total nem `hasNext`: o fim é a
//     página voltar menor que o pedido.
//   • As queries são a CÓPIA LITERAL das da página (as que ela compila em AST): introspecção
//     desligada e campo errado vira erro da query inteira.
//   • `bet.iid` = "sport:676297455" e o modal da aposta mostra "ID da Aposta: 676.297.455": o
//     código é o número. `payout` é o RETORNO; `createdAt` é a colocação em GMT.
//
// NÃO DECIDE NADA: normaliza o bilhete e sobe o cru (sem o `user`, que traz o nome da conta).
// Quem traduz é o `formatTicketSTC` (content.js) + `casas/CASA_STAKECOM.md`.
(function () {
  const _cruDe = new WeakMap();
  function _crus(lista) {
    const out = [];
    try {
      for (const b of lista || []) {
        const c = _cruDe.get(b);
        if (c && b.id) out.push({ codigo: String(b.id), cru: c });
      }
    } catch (e) {}
    return out;
  }

  const RX_GQL = /\/_api\/v1\/graphql$/i;
  const LIM_HIST = 20;                         // o da página (acima de 50 a casa devolve VAZIO)
  const LIM_ABERTAS = 50;                      // o da página, que é o teto medido
  const TETO_PAGINAS = 500;
  const STATUS_HIST = ["settled", "settledManual", "settledPending", "cancelPending", "cancelled", "cashout", "cashoutPending"];
  const Q_HIST = "query SportSportList($limit: Int!, $offset: Int!, $name: String, $status: [SportBetStatusEnum!], $filters: SportBetListFiltersInput) { user(name: $name) { __typename id name sportBetList(limit: $limit, offset: $offset, status: $status, filters: $filters) { __typename id iid bet { __typename ... on SportBet { __typename ...SportBet qrCodeUrl } ... on SwishBet { __typename ...SwishBetFragment ...SwishBetPartialCashout qrCodeUrl } ... on RacingBet { __typename ...RacingBet qrCodeUrl } ... on SportsbookXMultiBet { __typename ...XMultiBet qrCodeUrl } } } } } fragment SportBet on SportBet { __typename id customBet customPrices { __typename customOdds type promotion { __typename id name termsAndConditionsSlug tooltipDescription dsIconName type { code } rule { __typename boostLadder { __typename legs boost } } } stakeShield { __typename offerOdds protectionLevel } } amount activeAmount cashouts { __typename cashoutAmount } active currency status payoutMultiplier cashoutMultiplier cashoutDisabled updatedAt payout createdAt potentialMultiplier voidReason adjustments { __typename id payoutMultiplier updatedAt createdAt } promotionBet { __typename settleType status payout currency promotion { __typename name } } user { __typename id name } bet { __typename iid } outcomes { __typename id odds totalOdds status outcome { __typename ...SportMarketOutcome probabilities voidFactor payout } market { __typename ...SportMarket } fixture { __typename id name status slug provider marketCount(status: [active, suspended]) extId cashoutEnabled data { ...SportFixtureDataMatch ...SportFixtureDataOutright __typename } tournament { __typename ...TournamentTreeNested cashoutEnabled category { __typename sport { __typename slug cashoutEnabled cashoutConfiguration { __typename baseLoad cashoutEnabled varianceSensitivity } } } } eventStatus { __typename ...SportOutcomeFixtureEventStatus ...EsportOutcomeFixtureEventStatus } ...SportFixtureLiveStreamExists } } } fragment SportMarketOutcome on SportMarketOutcome { __typename id active odds probabilities name customBetAvailable } fragment SportMarket on SportMarket { __typename id name status extId specifiers customBetAvailable provider templateExtId } fragment SportFixtureDataMatch on SportFixtureDataMatch { startTime isOutright competitors { __typename ...SportFixtureCompetitor } teams { __typename extId name qualifier } __typename } fragment SportFixtureCompetitor on SportFixtureCompetitor { __typename name defaultName extId countryCode abbreviation iconPath country } fragment SportFixtureDataOutright on SportFixtureDataOutright { isOutright name startTime endTime __typename } fragment TournamentTreeNested on SportTournament { __typename id name slug category { __typename ...CategoryTreeNested cashoutEnabled } } fragment CategoryTreeNested on SportCategory { __typename id name slug sport { __typename id name slug } } fragment SportOutcomeFixtureEventStatus on SportFixtureEventStatusData { __typename homeScore awayScore matchStatus clock { __typename matchTime remainingTime } periodScores { __typename homeScore awayScore matchStatus } currentTeamServing homeGameScore awayGameScore statistic { __typename yellowCards { __typename away home } redCards { __typename away home } corners { __typename home away } } } fragment EsportOutcomeFixtureEventStatus on EsportFixtureEventStatus { matchStatus homeScore awayScore scoreboard { __typename homeGold awayGold homeGoals awayGoals homeKills awayKills gameTime homeDestroyedTowers awayDestroyedTurrets currentRound currentCtTeam currentDefTeam time awayWonRounds homeWonRounds remainingGameTime } periodScores { __typename type number awayGoals awayKills awayScore homeGoals homeKills homeScore awayWonRounds homeWonRounds matchStatus } __typename } fragment SportFixtureLiveStreamExists on SportFixture { __typename id stakeFixtureId streamExists } fragment SwishBetFragment on SwishBet { __typename active amount cashoutDisabled potentialMultiplier createdAt currency customBet id odds payout payoutMultiplier voidReason adjustments { __typename id payoutMultiplier updatedAt createdAt } promotionBet { __typename settleType status payout currency promotion { __typename name } } updatedAt status user { __typename id name preferenceHideBets } customPrices { __typename customOdds type promotion { __typename id name rule { __typename boostLadder { __typename legs boost } } } } outcomes { __typename id odds totalOdds lineType cancel outcome { __typename ...SwishMarketOutcomeFragment market { __typename data { __typename atBat { __typename marketDurationStart half inning pitcherName } } } } } } fragment SwishMarketOutcomeFragment on SwishMarketOutcome { __typename id line over under push gradeOver gradeUnder suspended balanced name competitor { __typename id name stats { __typename name dataConfirmed played starter } } market { __typename id game { __typename homeTeam awayTeam disabled status cashoutConfiguration { __typename baseLoad cashoutEnabled varianceSensitivity } } inPlay stat { __typename swishStatId name value type } game { __typename id fixture { __typename id extId name slug status provider streamExists swishGame { __typename swishSportId status } eventStatus { __typename ...SportFixtureEventStatus ...EsportFixtureEventStatus } data { __typename ... on SportFixtureDataMatch { __typename startTime isOutright teams { __typename extId name qualifier } competitors { __typename name extId countryCode abbreviation } } ... on SportFixtureDataOutright { __typename startTime isOutright name } } tournament { __typename id slug name category { __typename id slug name sport { __typename id name slug } } } } } } } fragment SportFixtureEventStatus on SportFixtureEventStatusData { __typename homeScore awayScore matchStatus clock { __typename matchTime remainingTime } periodScores { __typename homeScore awayScore matchStatus } currentTeamServing homeGameScore awayGameScore statistic { __typename yellowCards { __typename away home } redCards { __typename away home } corners { __typename home away } } } fragment EsportFixtureEventStatus on EsportFixtureEventStatus { matchStatus homeScore awayScore scoreboard { __typename homeGold awayGold homeGoals awayGoals homeKills awayKills gameTime homeDestroyedTowers awayDestroyedTowers homeDestroyedTurrets awayDestroyedTurrets currentRound currentCtTeam currentDefTeam time awayWonRounds homeWonRounds remainingGameTime } periodScores { __typename type number awayGoals awayKills awayScore homeGoals homeKills homeScore awayWonRounds homeWonRounds matchStatus } __typename } fragment SwishBetPartialCashout on SwishBet { __typename activeAmount cashouts { __typename cashoutAmount } } fragment RacingBet on RacingBet { __typename id active amount createdAt updatedAt currency resultType user { __typename id name } outcomes { __typename id updatedAt prices { __typename odds marketName } result { __typename resultedPrices status deadheatMultiplier } deductions { __typename key name percentage updatedAt } type derivativeType event { __typename id eventNumber slug startTime status stream { __typename url exists geoBlocked } runners { __typename scratched } meeting { __typename slug racing { __typename slug name } racingGroup { __typename slug name } venue { __typename name geoBlocked } category { __typename name slug } } topRunnerList(limit: 4) { __typename finalPosition runnerNumber } } selectionSlots { __typename runners { __typename ...RunnerOutcomeButton_RacingRunner } selections type } } payout payoutMultiplier adjustments { __typename id payoutMultiplier updatedAt createdAt } promotionBet { __typename settleType status payout currency promotion { __typename name } } betStatus: status betPotentialMultiplier: potentialMultiplier } fragment RunnerOutcomeButton_RacingRunner on RacingRunner { __typename id name scratched runnerNumber barrierPosition hcpDraw attributes { __typename weight } careerStats { __typename last6Runs } jockey { __typename name } trainer { __typename name } prices { __typename id active odds market { __typename name status } ...RunnerOutcomeButton_RacingOutcome } } fragment RunnerOutcomeButton_RacingOutcome on RacingOutcome { __typename id active odds market { __typename name status } } fragment XMultiBet on SportsbookXMultiBet { __typename id amount active currency _betStatus: status payoutMultiplier _potentialMultiplier: potentialMultiplier cashoutMultiplier cashoutDisabled updatedAt payout createdAt returnMultiplier customPrices { __typename customOdds type promotion { __typename id name rule { __typename boostLadder { __typename legs boost } } } } user { __typename id name } promotionBet { __typename settleType status payout currency promotion { __typename name } } adjustments { __typename id } outcomes { __typename id updatedAt providerBet { __typename id status sgm } ...SportBetOutcome_XMultiBet ...RacingBetOutcone_XMultiBet ...SwishBetOutcome_XMultiBetPrices } } fragment SportBetOutcome_XMultiBet on SportsbookXMultiBetOutcome { __typename result { __typename _status: status } _market: market { __typename ... on SportMarket { __typename status ...SportMarket } } _fixture: fixture { __typename ... on SportFixture { __typename id name status slug provider marketCount(status: [active, suspended]) extId cashoutEnabled data { ...SportFixtureDataMatch ...SportFixtureDataOutright __typename } tournament { __typename ...TournamentTreeNested cashoutEnabled category { __typename sport { __typename slug cashoutEnabled cashoutConfiguration { __typename baseLoad cashoutEnabled varianceSensitivity } } } } eventStatus { __typename ...SportOutcomeFixtureEventStatus ...EsportOutcomeFixtureEventStatus } ...SportFixtureLiveStreamExists } ... on SwishGame { __typename id } } prices { __typename id odds totalOdds outcome { __typename ... on SportMarketOutcome { __typename ...SportMarketOutcome probabilities voidFactor payout } } } } fragment RacingBetOutcone_XMultiBet on SportsbookXMultiBetOutcome { __typename runnerNumber _marketType: marketType _derivativeType: derivativeType prices { __typename odds _marketName: marketName outcome { __typename ... on RacingOutcome { __typename } } } result { __typename _status: status resultedPrices deadheatMultiplier } deductions { __typename key name percentage updatedAt } _selectionSlots: selectionSlots { __typename runners { __typename id finalPosition runnerNumber name scratched prices { __typename id active odds market { __typename name status } } } selections type } _event: fixture { __typename ... on RacingEvent { __typename id eventNumber slug startTime status stream { __typename url exists geoBlocked } runners { __typename scratched } meeting { __typename slug racing { __typename slug name } racingGroup { __typename slug name } venue { __typename name geoBlocked } category { __typename name slug } } topRunnerList(limit: 4) { __typename finalPosition runnerNumber } } } } fragment SwishBetOutcome_XMultiBetPrices on SportsbookXMultiBetOutcome { __typename prices { __typename lineType id odds totalOdds outcome { __typename ... on SwishMarketOutcome { __typename ...SwishMarketOutcomeFragment market { __typename data { __typename atBat { __typename marketDurationStart half inning pitcherName } } } } } } }";
  const Q_ABERTAS = "query ActiveBets_User($limit: Int!, $sort: UserBetsSortEnum, $name: String, $status: [SportBetStatusEnum!], $offset: Int!) { user(name: $name) { __typename id activeSportBets(limit: $limit, sort: $sort, offset: $offset) { __typename ...SportBetPreview_SportBet } activeSwishBetList(limit: $limit, sort: $sort, status: $status, offset: $offset) { __typename ...SwishBetPreview_SwishBet } activeRacingBets(limit: $limit, offset: $offset) { __typename ...RacingBetPreview_RacingBet } activeSportsbookXMultiBetList(limit: $limit, offset: $offset) { __typename ...XMultiBetPreview_SportsbookXMultiBet } } } fragment SportBetPreview_SportBet on SportBet { ...SportBetPreview_SportBetStreamed customBet cashoutDisabled amount currency payout potentialMultiplier payoutMultiplier cashoutMultiplier createdAt qrCodeUrl bet { __typename iid } user { __typename id } promotionBet { __typename status payout currency promotion { __typename name } } adjustments { __typename payoutMultiplier } outcomes { __typename fixture { __typename tournament { __typename category { __typename sport { __typename cashoutConfiguration { __typename cashoutEnabled baseLoad varianceSensitivity } } } } } } ...SportBetPreviewOutcomeGroup_SportBet } fragment SportBetPreview_SportBetStreamed on SportBet { __typename id active status voidReason activeAmount cashouts { __typename cashoutAmount } customPrices { __typename customOdds type stakeShield { __typename offerOdds protectionLevel } promotion { __typename id name type { code } dsIconName tooltipDescription termsAndConditionsSlug rule { __typename boostLadder { __typename legs boost } } } } } fragment SportBetPreviewOutcomeGroup_SportBet on SportBet { __typename outcomes { __typename id odds totalOdds status outcome { __typename id name odds active customBetAvailable probabilities voidFactor payout } market { __typename id name status extId specifiers customBetAvailable provider } fixture { __typename ...MatchInformation_SportFixture marketCount(status: [active, suspended]) cashoutEnabled eventStatus { __typename ...SportFixtureEventStatus ...EsportFixtureEventStatus } tournament { __typename id name cashoutEnabled category { __typename id name cashoutEnabled sport { __typename id name slug } } } data { __typename ... on SportFixtureDataMatch { __typename teams { __typename name qualifier } } ... on SportFixtureDataOutright { __typename endTime } } } } } fragment MatchInformation_SportFixture on SportFixture { __typename ...FixtureStatus_SportFixture ...FixtureOptions_SportFixture ...CompactScoreboard_SportFixture } fragment FixtureStatus_SportFixture on SportFixture { __typename id status ...FixtureOptions_SportFixture ...Live_SportFixture ...Active_SportFixture } fragment FixtureOptions_SportFixture on SportFixture { __typename ...FixtureOptionsOddin_SportFixture ...FixtureOptionsBetRadar_SportFixture } fragment FixtureOptionsOddin_SportFixture on SportFixture { __typename id extId stakeFixtureId name provider status widgetUrl liveWidgetUrl streamExists tournament { __typename id slug frontRowSeatEvent { __typename identifier } category { __typename slug sport { __typename slug } } } data { __typename ... on SportFixtureDataMatch { __typename competitors { __typename name abbreviation } startTime } ... on SportFixtureDataOutright { __typename name startTime } } } fragment FixtureOptionsBetRadar_SportFixture on SportFixture { __typename id extId stakeFixtureId name provider status widgetUrl liveWidgetUrl streamExists frontRowSeatFight { __typename fightId } tournament { __typename id slug frontRowSeatEvent { __typename identifier } category { __typename slug sport { __typename slug } } } data { __typename ... on SportFixtureDataMatch { __typename competitors { __typename name abbreviation } startTime } ... on SportFixtureDataOutright { __typename name startTime } } } fragment Live_SportFixture on SportFixture { __typename provider eventStatus { __typename ... on SportFixtureEventStatusData { __typename matchStatus periodScores { __typename matchStatus } clock { __typename matchTime remainingTime stopped } } ... on EsportFixtureEventStatus { __typename matchStatus periodScores { __typename matchStatus } scoreboard { __typename gameTime remainingGameTime } } } tournament { __typename category { __typename sport { __typename slug } } } } fragment Active_SportFixture on SportFixture { __typename data { __typename ... on SportFixtureDataOutright { __typename endTime } ... on SportFixtureDataMatch { __typename startTime } } } fragment CompactScoreboard_SportFixture on SportFixture { __typename ...FixtureScoreboard_SportFixture ...CricketScoreboard_SportFixture } fragment FixtureScoreboard_SportFixture on SportFixture { __typename ...FixtureCompetitors_SportFixture status eventStatus { __typename ... on SportFixtureEventStatusData { __typename homeScore awayScore matchStatus homeGameScore awayGameScore periodScores { __typename homeScore awayScore } } ... on EsportFixtureEventStatus { __typename homeScore awayScore periodScores { __typename homeScore awayScore } scoreboard { __typename homeKills homeWonRounds awayKills awayWonRounds } } } } fragment FixtureCompetitors_SportFixture on SportFixture { __typename id name slug provider tournament { __typename slug category { __typename slug sport { __typename slug } } } eventStatus { __typename ... on SportFixtureEventStatusData { __typename currentTeamServing } } data { __typename ... on SportFixtureDataMatch { __typename isOutright teams { __typename extId name qualifier } competitors { __typename ...CompetitorIcon_SportFixtureCompetitor } } ... on SportFixtureDataOutright { __typename isOutright } } } fragment CompetitorIcon_SportFixtureCompetitor on SportFixtureCompetitor { __typename name defaultName extId iconPath countryCode country } fragment CricketScoreboard_SportFixture on SportFixture { __typename ...Competitors_SportFixture status tournament { __typename category { __typename sport { __typename slug } } } eventStatus { __typename ... on SportFixtureEventStatusData { __typename matchStatus } } } fragment Competitors_SportFixture on SportFixture { __typename ...FixtureCompetitors_SportFixture extId eventStatus { __typename ... on SportFixtureEventStatusData { __typename matchStatus } } } fragment SportFixtureEventStatus on SportFixtureEventStatusData { __typename homeScore awayScore matchStatus clock { __typename matchTime remainingTime } periodScores { __typename homeScore awayScore matchStatus } currentTeamServing homeGameScore awayGameScore statistic { __typename yellowCards { __typename away home } redCards { __typename away home } corners { __typename home away } } } fragment EsportFixtureEventStatus on EsportFixtureEventStatus { matchStatus homeScore awayScore scoreboard { __typename homeGold awayGold homeGoals awayGoals homeKills awayKills gameTime homeDestroyedTowers awayDestroyedTowers homeDestroyedTurrets awayDestroyedTurrets currentRound currentCtTeam currentDefTeam time awayWonRounds homeWonRounds remainingGameTime } periodScores { __typename type number awayGoals awayKills awayScore homeGoals homeKills homeScore awayWonRounds homeWonRounds matchStatus } __typename } fragment SwishBetPreview_SwishBet on SwishBet { ...SwishBetPreview_SwishBetStreamed customBet cashoutDisabled payoutMultiplier payout odds amount currency createdAt qrCodeUrl user { __typename id } promotionBet { __typename status payout currency promotion { __typename name } } adjustments { __typename payoutMultiplier } outcomes { __typename ...SwishBetPreviewOutcomeGroup_SwishBetOutcome } } fragment SwishBetPreview_SwishBetStreamed on SwishBet { __typename id active status voidReason activeAmount cashouts { __typename cashoutAmount } customPrices { __typename customOdds type promotion { __typename id name rule { __typename boostLadder { __typename legs boost } } } } } fragment SwishBetPreviewOutcomeGroup_SwishBetOutcome on SwishBetOutcome { __typename id odds totalOdds lineType outcome { __typename ...SwishBetPreviewOutcomeGroup_SwishMarketOutcome } } fragment SwishBetPreviewOutcomeGroup_SwishMarketOutcome on SwishMarketOutcome { __typename id line over under push gradeOver gradeUnder suspended balanced name competitor { __typename id name stats { __typename name dataConfirmed played starter } } market { __typename id inPlay stat { __typename swishStatId name value type } data { __typename atBat { __typename marketDurationStart half inning pitcherName } } game { __typename id disabled status homeTeam awayTeam cashoutConfiguration { __typename cashoutEnabled baseLoad varianceSensitivity } fixture { __typename ...MatchInformation_SportFixture eventStatus { __typename ...SportFixtureEventStatus ...EsportFixtureEventStatus } tournament { __typename slug category { __typename name } } swishGame { __typename swishSportId status } data { __typename ... on SportFixtureDataMatch { __typename teams { __typename name qualifier } } ... on SportFixtureDataOutright { __typename name } } } } } } fragment RacingBetPreview_RacingBet on RacingBet { __typename active betStatus: status betPotentialMultiplier: potentialMultiplier resultType payout payoutMultiplier amount currency createdAt id qrCodeUrl user { __typename id } adjustments { __typename payoutMultiplier } promotionBet { __typename status payout currency promotion { __typename name } } outcomes { __typename event { __typename runners { __typename scratched } } selectionSlots { __typename selections } } ...RacingBetPreviewOutcome_RacingBet } fragment RacingBetPreviewOutcome_RacingBet on RacingBet { __typename id outcomes { __typename id type derivativeType prices { __typename odds marketName } result { __typename status resultedPrices } deductions { __typename key percentage updatedAt } selectionSlots { __typename runners { __typename id name runnerNumber scratched } } event { __typename id slug eventNumber startTime status stream { __typename exists url geoBlocked } topRunnerList { __typename finalPosition runnerNumber } meeting { __typename slug racing { __typename slug name } racingGroup { __typename slug } venue { __typename name } category { __typename slug } } } } } fragment XMultiBetPreview_SportsbookXMultiBet on SportsbookXMultiBet { __typename id amount active currency customPrices { __typename customOdds type promotion { __typename id name rule { __typename boostLadder { __typename legs boost } } } } _betStatus: status payoutMultiplier _potentialMultiplier: potentialMultiplier cashoutMultiplier cashoutDisabled updatedAt payout createdAt qrCodeUrl returnMultiplier user { __typename id name } promotionBet { __typename settleType status payout currency promotion { __typename name } } adjustments { __typename id } outcomes { __typename id updatedAt ...SportBetOutcome_XMultiBet ...RacingBetOutcone_XMultiBet ...SwishBetOutcome_XMultiBet providerBet { __typename id status sgm } } } fragment SportBetOutcome_XMultiBet on SportsbookXMultiBetOutcome { __typename result { __typename _status: status } _market: market { __typename ... on SportMarket { __typename status ...SportMarket } } _fixture: fixture { __typename ... on SportFixture { __typename id name status slug provider marketCount(status: [active, suspended]) extId cashoutEnabled data { ...SportFixtureDataMatch ...SportFixtureDataOutright __typename } tournament { __typename ...TournamentTreeNested cashoutEnabled category { __typename sport { __typename slug cashoutEnabled cashoutConfiguration { __typename baseLoad cashoutEnabled varianceSensitivity } } } } eventStatus { __typename ...SportOutcomeFixtureEventStatus ...EsportOutcomeFixtureEventStatus } ...SportFixtureLiveStreamExists } ... on SwishGame { __typename id } } prices { __typename id odds totalOdds outcome { __typename ... on SportMarketOutcome { __typename ...SportMarketOutcome probabilities voidFactor payout } } } } fragment SportMarket on SportMarket { __typename id name status extId specifiers customBetAvailable provider templateExtId } fragment SportFixtureDataMatch on SportFixtureDataMatch { startTime isOutright competitors { __typename ...SportFixtureCompetitor } teams { __typename extId name qualifier } __typename } fragment SportFixtureCompetitor on SportFixtureCompetitor { __typename name defaultName extId countryCode abbreviation iconPath country } fragment SportFixtureDataOutright on SportFixtureDataOutright { isOutright name startTime endTime __typename } fragment TournamentTreeNested on SportTournament { __typename id name slug category { __typename ...CategoryTreeNested cashoutEnabled } } fragment CategoryTreeNested on SportCategory { __typename id name slug sport { __typename id name slug } } fragment SportOutcomeFixtureEventStatus on SportFixtureEventStatusData { __typename homeScore awayScore matchStatus clock { __typename matchTime remainingTime } periodScores { __typename homeScore awayScore matchStatus } currentTeamServing homeGameScore awayGameScore statistic { __typename yellowCards { __typename away home } redCards { __typename away home } corners { __typename home away } } } fragment EsportOutcomeFixtureEventStatus on EsportFixtureEventStatus { matchStatus homeScore awayScore scoreboard { __typename homeGold awayGold homeGoals awayGoals homeKills awayKills gameTime homeDestroyedTowers awayDestroyedTurrets currentRound currentCtTeam currentDefTeam time awayWonRounds homeWonRounds remainingGameTime } periodScores { __typename type number awayGoals awayKills awayScore homeGoals homeKills homeScore awayWonRounds homeWonRounds matchStatus } __typename } fragment SportFixtureLiveStreamExists on SportFixture { __typename id stakeFixtureId streamExists } fragment SportMarketOutcome on SportMarketOutcome { __typename id active odds probabilities name customBetAvailable } fragment RacingBetOutcone_XMultiBet on SportsbookXMultiBetOutcome { __typename runnerNumber _marketType: marketType _derivativeType: derivativeType prices { __typename odds _marketName: marketName outcome { __typename ... on RacingOutcome { __typename } } } result { __typename _status: status resultedPrices deadheatMultiplier } deductions { __typename key name percentage updatedAt } _selectionSlots: selectionSlots { __typename runners { __typename id finalPosition runnerNumber name scratched prices { __typename id active odds market { __typename name status } } } selections type } _event: fixture { __typename ... on RacingEvent { __typename id eventNumber slug startTime status stream { __typename url exists geoBlocked } runners { __typename scratched } meeting { __typename slug racing { __typename slug name } racingGroup { __typename slug name } venue { __typename name geoBlocked } category { __typename name slug } } topRunnerList(limit: 4) { __typename finalPosition runnerNumber } } } } fragment SwishBetOutcome_XMultiBet on SportsbookXMultiBetOutcome { __typename prices { __typename id odds totalOdds lineType outcome { __typename ... on SwishMarketOutcome { __typename ...SwishBetPreviewOutcomeGroup_SwishMarketOutcome } } } }";
  const LISTAS_ABERTAS = ["activeSportBets", "activeSwishBetList", "activeRacingBets", "activeSportsbookXMultiBetList"];

  const byId = new Map();
  let respostas = 0;
  let token = "";
  let pedido = false, loopAtivo = false, fimReplay = false, repetir = false;
  let erro = "";
  const LOG = (...a) => { try { console.log("[SharpenUp stc_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;

  // ── normalização ─────────────────────────────────────────────────────────────
  const _n = (v) => { if (v == null || v === "") return null; const x = Number(v); return isFinite(x) ? x : null; };
  const _s = (v) => (v == null ? "" : String(v));
  const _limpo = (v) => _s(v).replace(/\s+/g, " ").trim();
  const _quando = (v) => { const t = Date.parse(_s(v)); return isFinite(t) ? Math.floor(t / 1000) : null; };
  const _caminho = (u) => { try { return new URL(_s(u), location.href).pathname; } catch (e) { return ""; } };

  // "sport:676297455" → "676297455" (o "ID da Aposta" do modal). Outro prefixo sobe inteiro.
  function _codigo(iid, id) {
    const s = _s(iid);
    const m = s.match(/^sport:(\d+)$/);
    return m ? m[1] : (s ? s.replace(/[^\w-]+/g, "-") : _s(id));
  }

  function _fixture(f) {
    const fx = f || {};
    const tor = fx.tournament || {};
    const sp = (tor.category && tor.category.sport) || {};
    const dados = fx.data || {};
    return { jogo: _limpo(fx.name || dados.name), liga: _limpo(tor.name), esporte: _limpo(sp.name),
             esporteSlug: _s(sp.slug), inicio: _quando(dados.startTime) };
  }

  function pernaSport(o) {
    const fx = _fixture(o.fixture);
    return {
      status: _s(o.status),                     // pending · won · lost … (CRU)
      anulada: _n(o.outcome && o.outcome.voidFactor),
      odd: _n(o.odds),
      selecao: _limpo(o.outcome && o.outcome.name),
      mercado: _limpo(o.market && o.market.name),
      jogo: fx.jogo, liga: fx.liga, esporte: fx.esporte, inicio: fx.inicio,
    };
  }

  function pernaSwish(o) {
    const out = o.outcome || {};
    const game = (out.market && out.market.game) || {};
    const fx = _fixture(game.fixture);
    return {
      status: o.cancel ? "cancel" : "",         // a perna de props não diz ganha/perdida
      anulada: o.cancel ? 1 : 0,
      odd: _n(o.odds),
      jogador: _limpo(out.competitor && out.competitor.name),
      estatistica: _limpo(out.name),            // "rebounds", "assists" (inglês da casa)
      linha: _n(out.line),
      lado: _s(o.lineType),                     // over · under
      jogo: fx.jogo || [game.homeTeam, game.awayTeam].filter(Boolean).join(" - "),
      liga: fx.liga, esporte: fx.esporte, inicio: fx.inicio,
    };
  }

  function parseBet(iid, b) {
    if (!b || !b.id) return null;
    const tipo = _s(b.__typename);
    const outs = Array.isArray(b.outcomes) ? b.outcomes : [];
    const pot = _n(b.potentialMultiplier != null ? b.potentialMultiplier
              : (b._potentialMultiplier != null ? b._potentialMultiplier : b.betPotentialMultiplier));
    return {
      id: _codigo(iid || (b.bet && b.bet.iid), b.id),
      tipo: tipo,                               // SportBet · SwishBet · RacingBet · SportsbookXMultiBet
      status: _s(b.status || b._betStatus || b.betStatus),
      ativa: b.active === true,
      moeda: _s(b.currency).toUpperCase(),
      stake: _n(b.amount),
      retorno: _n(b.payout),
      odd: tipo === "SwishBet" && _n(b.odds) != null ? _n(b.odds) : pot,
      criarAposta: b.customBet === true,
      anulacao: _s(b.voidReason),
      promocao: !!(b.promotionBet || (Array.isArray(b.customPrices) && b.customPrices.length) ||
                   (Array.isArray(b.adjustments) && b.adjustments.length)),
      cashoutParcial: Array.isArray(b.cashouts) && b.cashouts.length > 0,
      colocada: _quando(b.createdAt),
      pernas: tipo === "SportBet" ? outs.map(pernaSport)
            : tipo === "SwishBet" ? outs.map(pernaSwish) : [],
    };
  }

  function _semUsuario(b) {
    const c = {};
    for (const k of Object.keys(b)) if (k !== "user") c[k] = b[k];
    return c;
  }

  function enviar() {
    try {
      window.postMessage({
        __sharpenupSTCData: true, hook: true,
        bilhetes: Array.from(byId.values()), respostas: respostas, fim: fimReplay,
        cru: _crus(Array.from(byId.values())),
        semToken: !_token(), erro: erro,
      }, "*");
    } catch (e) {}
  }

  // A versão LIQUIDADA vence a ABERTA.
  function guardar(b) {
    const ex = byId.get(b.id);
    if (!ex || ex.ativa || !b.ativa) byId.set(b.id, b);
  }

  function _registrar(iid, raw) {
    const b = parseBet(iid, raw);
    if (!b) return;
    // O cru leva o `iid` ao lado: no histórico ele mora FORA do objeto da aposta, e a props
    // (`SwishBet`) não traz `bet.iid`. Sem ele a Ficha não teria o código.
    try { _cruDe.set(b, { iid: _s(iid || (raw.bet && raw.bet.iid)), bet: _semUsuario(raw) }); } catch (e) {}
    guardar(b);
  }

  // Lê uma resposta. Devolve `{historico, abertas:{lista:n}}`, `{erro}` ou null (não é lista).
  function consumir(text) {
    if (typeof text !== "string" || !/sportBetList|activeSportBets/.test(text)) return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    const u = j && j.data && j.data.user;
    if (!u) {
      if (j && Array.isArray(j.errors) && j.errors.length) return { erro: _s(j.errors[0] && j.errors[0].message) };
      return { erro: "a casa não devolveu o usuário: sessão expirada ou sem login" };
    }
    const res = { historico: null, abertas: {} };
    if (Array.isArray(u.sportBetList)) {
      res.historico = u.sportBetList.length;
      for (const x of u.sportBetList) if (x && x.bet) _registrar(x.iid, x.bet);
    }
    for (const k of LISTAS_ABERTAS) {
      if (!Array.isArray(u[k])) continue;
      res.abertas[k] = u[k].length;
      for (const b of u[k]) _registrar(b && b.bet && b.bet.iid, b);
    }
    if (res.historico == null && !Object.keys(res.abertas).length) return null;
    respostas++;
    LOG("resposta:", JSON.stringify(res), "· total:", byId.size);
    enviar();
    return res;
  }

  // ── aprendizado ────────────────────────────────────────────────────────────────
  function aprender(url, headers) {
    if (!RX_GQL.test(_caminho(url))) return;
    for (const k of Object.keys(headers || {})) {
      if (k.toLowerCase() !== "x-access-token") continue;
      const v = _s(headers[k]).trim();
      if (v) { if (!token) LOG("token aprendido"); token = v; }
    }
    if (_token() && pedido) arrancarReplay();
  }

  // Partida a frio: a sessão é o cookie `session` (medido). A chamada real manda.
  function _token() {
    if (token) return token;
    try {
      const c = _s(document.cookie).split(/;\s*/).find((x) => x.indexOf("session=") === 0);
      return c ? decodeURIComponent(c.slice(8)).trim() : "";
    } catch (e) { return ""; }
  }

  const _lang = () => (_caminho(location.href).match(/^\/([a-z]{2})(\/|$)/i) || [])[1] || "pt";

  // ── replay ─────────────────────────────────────────────────────────────────────
  async function pedir(query, variables) {
    const r = await of.call(window, location.origin + "/_api/v1/graphql", {
      method: "POST", credentials: "include",
      headers: { accept: "*/*", "content-type": "application/json", "x-access-token": _token(), "x-language": _lang() },
      body: JSON.stringify({ query: query, variables: variables }),
    });
    return { ok: !!(r && r.ok), status: r && r.status, text: r ? await r.text() : "" };
  }

  async function ler(query, variables) {
    let r;
    try { r = await pedir(query, variables); }
    catch (e) { erro = "replay falhou: " + (e && e.message); LOG(erro); return null; }
    if (!r.ok) { erro = "replay parou · HTTP " + r.status; LOG(erro); return null; }
    const res = consumir(r.text);
    if (!res) {
      // Sessão vencida volta `{errors, data:{user:null}}`, sem o nome da lista: a mensagem da casa
      // é o diagnóstico, não "formato desconhecido".
      let msg = "";
      try { const j = JSON.parse(r.text); msg = j && Array.isArray(j.errors) && j.errors[0] ? _s(j.errors[0].message) : ""; } catch (e) {}
      erro = msg ? "a casa respondeu erro: " + msg : "resposta da lista em formato desconhecido";
      LOG(erro); return null;
    }
    if (res.erro) { erro = "a casa respondeu erro: " + res.erro; LOG(erro); return null; }
    return res;
  }

  async function varrer() {
    // Histórico: pelo tamanho que VOLTOU; página menor que a pedida = fim.
    for (let p = 0, off = 0; p < TETO_PAGINAS; p++) {
      const res = await ler(Q_HIST, { limit: LIM_HIST, offset: off, status: STATUS_HIST, filters: {} });
      if (!res) return false;
      if (res.historico < LIM_HIST) break;
      off += res.historico;
    }
    // Abertas: as quatro listas andam juntas; acaba quando todas voltam menores que o pedido.
    for (let p = 0, off = 0; p < TETO_PAGINAS; p++) {
      const res = await ler(Q_ABERTAS, { limit: LIM_ABERTAS, offset: off, sort: "placedTime" });
      if (!res) return false;
      const ns = LISTAS_ABERTAS.map((k) => res.abertas[k] || 0);
      if (Math.max.apply(null, ns) < LIM_ABERTAS) break;
      off += LIM_ABERTAS;
    }
    return true;
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !_token()) return;
    loopAtivo = true;
    erro = "";
    try { await varrer(); }
    finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();
      if (repetir) { repetir = false; fimReplay = false; byId.clear(); arrancarReplay(); }
    }
  }

  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupSTCReq) return;
    pedido = true;
    if (loopAtivo) repetir = true;
    else { fimReplay = false; if (_token()) byId.clear(); }
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  const _hdrsToObj = (h) => {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  };
  if (of && !of.__suSTCW) {
    const w = function (...a) {
      const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
      const url = req ? req.url : a[0];
      const opts = a[1] || {};
      try { aprender(url, _hdrsToObj(opts.headers || (req && req.headers))); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try {
          if (RX_GQL.test(_caminho(url))) {
            // 2º argumento SEMPRE: sem ele um clone abortado vira rejeição muda (s305).
            r.clone().text().then((t) => { const x = consumir(t); if (x && x.erro) LOG("lista da página:", x.erro); }, () => {});
          }
        } catch (e) {}
        return r;
      });
    };
    w.__suSTCW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ── (rede de segurança)
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suSTCW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suSTCU = u; this.__suSTCH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suSTCH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        aprender(this.__suSTCU, this.__suSTCH);
        if (RX_GQL.test(_caminho(this.__suSTCU))) {
          this.addEventListener("load", () => {
            try { consumir((this.responseType === "" || this.responseType === "text") ? this.responseText : JSON.stringify(this.response)); } catch (e) {}
          });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suSTCW = true;
    XMLHttpRequest.prototype.send = s;
  }

  enviar();
})();
