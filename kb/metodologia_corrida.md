# Metodologia de Corrida do GoJohnny

## Objetivo do arquivo

Este é o **núcleo técnico** do GoJohnny. Aqui está como o treinador pensa: princípios, estrutura semanal, distribuição de intensidade, evolução, recuperação, objetivos por distância e heurísticas de decisão.

O foco é o corredor recreativo — iniciante ou intermediário — que quer evoluir com segurança, consistência e controle. Nada de fórmula mágica. Nada de plano de elite enfiado em quem corre 3x por semana.

## Quando o GPT deve consultar este arquivo

- Ao desenhar ou ajustar plano semanal.
- Ao decidir se o atleta deve evoluir, manter ou reduzir carga.
- Ao analisar uma semana fechada e propor a próxima.
- Ao explicar para o atleta por que um treino existe ou foi prescrito daquele jeito.
- Quando o atleta pedir mais volume, mais intensidade ou mudança de abordagem.
- Antes de prescrever ciclo para uma prova alvo.
- Para decidir se um sintoma (dor, fadiga, baixa aderência) muda ou não a prescrição.

## Quando este arquivo NÃO deve ser usado como fonte principal

- Para detalhar **um tipo de treino específico** (regenerativo, longo, tiro, limiar). Use `tipos_de_treino.md`.
- Para decidir **o que salvar como memória**. Use `memoria.md`.
- Para consultar **dados do atleta**: plano ativo, histórico, perfil. Use a API.
- Para diagnosticar lesão. Não é função do GoJohnny.

## Relação com a API

A API entrega o **estado atual do atleta**: nível, objetivo, plano vigente, histórico de execução, memórias relevantes, prova alvo. Este arquivo entrega os **critérios técnicos** para interpretar esse estado e decidir o próximo passo.

Sem a API, este arquivo é teoria. Sem este arquivo, a API é dado solto. A combinação é o que faz o GoJohnny treinar de verdade.

## Princípios centrais

1. **Consistência antes de intensidade.** Treinar regularmente vale mais que treinar forte.
2. **Segurança antes de performance.** Dor muda a prioridade. Fadiga alta muda a semana.
3. **Controle de esforço antes de pace bonito.** Pace é consequência, não objetivo do treino-base.
4. **Recuperação faz parte do treino.** Adaptação acontece no descanso, não no esforço.
5. **Regenerativo precisa ser leve.** Se sai forte, virou outro treino.
6. **Longão precisa construir base.** Não é prova nem palco para provar nada.
7. **Intensidade deve ter propósito.** Tiro por tiro, sem objetivo, é desgaste.
8. **Especificidade.** Treino se aproxima da demanda da prova conforme o ciclo avança.
9. **Sobrecarga progressiva controlada.** Aumenta o que o corpo já tolera.
10. **Individualização.** Não existe plano universal. Existe plano calibrado.
11. **Adaptação contínua.** O plano serve ao atleta, não o contrário.
12. **Histórico guia o futuro.** Padrão recorrente pesa mais que evento isolado.
13. **Nem todo erro exige mudar o plano.** Padrão pede ajuste; oscilação não.
14. **Treino bom gera adaptação, não só cansaço.**

## Princípios do treinamento (aplicados)

- **Especificidade.** Quem treina para 21k corre longo, controla pace e treina ritmo de prova nas semanas-chave. Quem treina para 5k tolera mais intensidade próxima do limiar e VO2.
- **Sobrecarga progressiva.** Aumento de volume típico: 5-10% por semana, com semana regenerativa a cada 3-4 semanas. Aumento de intensidade só quando o volume está consolidado.
- **Recuperação.** Sem recuperação, não há adaptação. Treino forte sem descanso é só desgaste.
- **Individualidade.** Mesmo treino, dois atletas, duas respostas. Calibre pelo histórico.
- **Reversibilidade.** Ganhos perdem-se sem manutenção. Em pausas longas, retomar conservador.
- **Variação.** Estímulos variados (zona 2, limiar, VO2, força) constroem corredor mais completo. Sem virar bagunça.
- **Consistência.** O parâmetro mais importante. Plano que não cabe na vida não treina ninguém.
- **Controle de intensidade.** Maior parte do volume em esforço leve/controlado. Intensidade dosada e proposital.

## Estrutura de uma semana (por nº de treinos)

Use estas estruturas como ponto de partida. Ajuste para o atleta real.

### 2 treinos por semana
- 1 treino leve ou base controlada (4-6 km).
- 1 longo/base (6-12 km dependendo do objetivo e nível).

Foco: criar hábito, construir base, evitar lesão. Volume baixo e intensidade controlada.

### 3 treinos por semana
- 1 treino leve / regenerativo (4-6 km).
- 1 treino de qualidade ou base controlada (fartlek leve, ritmo controlado, ou base mais firme — depende do nível).
- 1 longo (8-15 km).

Foco: equilíbrio entre estímulo e recuperação. Estrutura típica do corredor recreativo regular.

### 4 treinos por semana
- 2 leves (5-7 km cada).
- 1 qualidade (intervalado leve, fartlek, limiar curto, conforme fase).
- 1 longo (10-18 km).

Foco: começa a permitir variação real de estímulos. Atenção redobrada a recuperação entre qualidade e longo.

### 5-6 treinos por semana
- 3 a 4 treinos leves/base.
- 1 a 2 qualidades distribuídas com pelo menos 48h entre si.
- 1 longo.

Foco: maior parte do volume em intensidade leve. Qualidade bem dosada. Recuperação monitorada de perto. Sem isso, vira poço de fadiga.

**Regra prática transversal:**
- Nunca empilhe 2 treinos fortes em dias seguidos sem propósito claro.
- Sempre tenha pelo menos 1 dia totalmente off ou de leve absoluto na semana.
- Longo sempre depois de pelo menos 1 dia leve ou off.

## Filosofia de intensidade

A maior parte do treino deve ser **leve e controlada**. Intensidade existe, mas é uma fatia pequena, dosada e com propósito.

**Erros mais comuns do recreativo:**
- Correr tudo em moderado (zona "cinza"). Cansa, não constrói base, não desenvolve velocidade.
- Transformar regenerativo em moderado. Não recupera nada.
- Transformar longão em ritmo de prova. Cansa demais e não constrói base aeróbica.
- Subir volume e intensidade ao mesmo tempo. Gera fadiga e risco de lesão.

**Sobre 80/20, polarizado, piramidal:**
- 80/20 (≈80% leve, 20% intenso) é uma boa referência **conceitual**, não dogma.
- Modelo polarizado (volume leve + alguns picos altos, pouco moderado) tem evidência sólida em endurance.
- Modelo piramidal (mais leve, alguma quantidade de moderado, pouca intensidade alta) também funciona bem para recreativos.
- O que importa: **a maior parte do volume em zona leve/aeróbica**. Intensidade alta dosada. Pouco tempo na "zona cinza" sem objetivo.

A distribuição certa depende de:
- Nível do atleta (iniciante absorve menos intensidade).
- Objetivo (5k tolera mais VO2; 42k pede mais base).
- Fase do ciclo (base, específico, taper).
- Histórico recente (semana cansada → menos intensidade).

## Como o GoJohnny decide evolução

Antes de aumentar carga, verifique se o atleta está pronto. Use os 3 estados:

### EVOLUIR — pode subir carga
Todos os critérios verdadeiros:
- Aderência ao plano nas últimas 2-3 semanas ≥ 80%.
- Cansaço dentro do esperado, sem fadiga crescente.
- Sem dor relevante.
- Treinos leves saíram realmente leves.
- Longos foram bem executados (não viraram prova).
- Atleta consegue cumprir o plano sem colapsar no fim da semana.

Subida típica: +5-10% de volume na semana, ou inserção de qualidade nova bem dosada.

### MANTER — semana parecida com a anterior
Algum dos critérios:
- Atleta cumpriu o plano, mas com intensidade um pouco alta demais em treinos-base.
- Houve dificuldade de controle em 1+ treino.
- Houve cansaço moderado no fim da semana.
- Semana teve oscilação (perdeu 1 treino, executou outro pesado).

Manutenção é normal. Nem toda semana é evolução.

### REDUZIR — baixar carga ou inserir regenerativa
Algum dos critérios:
- Dor relevante.
- Fadiga alta sustentada.
- Aderência abaixo de 60%.
- Sono ruim recorrente.
- Carga emocional alta vinda da vida (trabalho, família, viagem).
- Treinos saindo bem acima do prescrito repetidamente.
- Pós-prova recente.

Redução não é fracasso. É inteligência.

**Heurística:** quando em dúvida entre evoluir e manter, mantenha. Quando em dúvida entre manter e reduzir, reduza.

## Metodologia por objetivo

### 5k
- **Foco:** velocidade e tolerância a esforço alto.
- **Distribuição:** mais espaço para limiar, VO2 e tiros curtos, sem abandonar base.
- **Longo:** moderado em volume (até ~10-12 km, dependendo do nível).
- **Frequência típica:** 3-4 treinos/semana.
- **Cuidado:** corredor recreativo iniciante deve construir base antes de buscar tiro.

### 10k
- **Foco:** equilíbrio entre limiar e base aeróbica.
- **Distribuição:** longo, treinos de ritmo sustentado, alguns intervalados longos (1k, 1,2k, 1,5k).
- **Longo:** 12-15 km típico no pico.
- **Frequência típica:** 3-5 treinos/semana.

### 21k (foco principal do GoJohnny)
- **Foco:** base aeróbica forte + capacidade de sustentar ritmo.
- **Distribuição:**
  - Maioria do volume em leve/controlado.
  - Longos progressivos ao longo do ciclo (de 10 km até 18-20 km no pico, dependendo do nível).
  - Treinos de limiar e ritmo sustentado nas semanas-chave, **só quando há base**.
  - Ritmo de prova trabalhado nas semanas finais antes do taper.
- **Ciclo típico:** 12-16 semanas para um corredor com base. 16-20 semanas se está construindo do zero ou retornando.
- **Estrutura:** 3 semanas de carga + 1 regenerativa, repetindo.
- **Taper:** redução de volume progressiva nas 2 últimas semanas, mantendo um pouco de intensidade.
- **Força:** integrar 1-2 sessões de força/semana ao longo do ciclo.

### 42k
- **Foco:** base aeróbica muito forte, gestão de fadiga, capacidade de tempo em pé.
- **Distribuição:** volume considerável em leve, longos longos (até 28-32 km dependendo do plano), treinos de ritmo de maratona em semanas-chave.
- **Frequência típica:** mínimo 4 treinos/semana, idealmente 5.
- **Cuidado:** maratona não é para qualquer um em qualquer momento. Exige histórico, base e tempo.

## O papel da força

Treino de força ajuda corredor recreativo:
- Tolerância à carga (menos sobrecarga em joelho, tibial, panturrilha).
- Economia de corrida.
- Estabilidade de quadril, core, tornozelo.
- Prevenção de excesso e lesões por repetição.
- Sustentação de volume em ciclos mais longos.

**Diretriz geral do GoJohnny:** 1-2 sessões de força/semana, focando em padrões funcionais (agachamento, afundo, ponte, prancha, panturrilha). 30-45 minutos é suficiente para o recreativo.

**Não prescreva treino detalhado de musculação.** O GoJohnny dá orientação geral e direciona ao profissional quando o atleta precisa de plano específico.

## Heurísticas do treinador

Estas são regras práticas. Aplique sempre que a situação se encaixar:

- **Se o atleta acelera todo regenerativo, não aumente intensidade na semana seguinte.** Trabalhe controle primeiro.
- **Se o longão vira progressivo sem ser pedido, reforce controle e mantenha plano.** Não recompense execução errada com mais carga.
- **Se o atleta termina todos os treinos em zona alta, reduza ambição da semana.** Ele está dizendo que o plano está acima da capacidade atual.
- **Se a semana foi consistente, controlada e sem dor, pode evoluir.**
- **Se o atleta completou tudo mas terminou muito cansado, mantenha — não evolua.**
- **Se há dor, reduza ou substitua.** Sempre. Sem heroísmo.
- **Se há prova recente (≤7 dias), recupere primeiro, treine depois.**
- **Quando em dúvida entre carga e descanso, descanse.**
- **Treino que o atleta não consegue cumprir 3 vezes seguidas é treino mal prescrito.** Ajuste a prescrição, não pressione o atleta.
- **Plano agressivo só com histórico que sustente.** Motivação não basta.
- **Sem dor é informação. Com dor, é prioridade.**

## Matriz de decisão semanal

| Aderência | Cansaço | Dor | Decisão |
|---|---|---|---|
| ≥80% | Normal | Não | Evoluir |
| ≥80% | Alto | Não | Manter |
| ≥80% | Normal | Leve pontual | Manter, monitorar |
| 60-80% | Normal | Não | Manter |
| 60-80% | Alto | Não | Reduzir |
| <60% | Qualquer | Qualquer | Reduzir e revisar plano vs realidade |
| Qualquer | Qualquer | Persistente / forte | Reduzir, substituir treino de impacto, sugerir profissional |

## Exemplos práticos

### Exemplo 1 — Atleta cumpriu 3/3, tudo forte demais
**Contexto:** plano pedia 1 leve, 1 fartlek, 1 longo controlado. Atleta fez tudo em pace alto, regenerativo virou moderado, longo virou progressivo.
**Leitura técnica:** aderência alta mas controle baixo. Está treinando em zona cinza permanente.
**Decisão:** **manter** volume, **não evoluir** intensidade. Reforçar instrução de controle. Possivelmente registrar erro_recorrente se já se repetiu.
**Resposta sugerida:** "Treinos feitos, mas todos saíram mais firmes que o pedido. Antes de subir a régua, preciso te ver controlando. Mesmo plano essa semana, foco no pace certo nos leves."

### Exemplo 2 — Atleta fez 2/3 e está bem
**Contexto:** atleta executou bem o longo e o leve, perdeu o de qualidade. Sem dor, sem cansaço.
**Leitura técnica:** aderência ok, qualidade da execução boa, perda eventual.
**Decisão:** **manter**, sem drama. Possivelmente reposicionar o treino perdido.
**Resposta sugerida:** "Boa, o que fez tava bem feito. Próxima semana mantemos o mesmo desenho — só não pula a qualidade duas vezes seguidas."

### Exemplo 3 — Longão executado controlado pela primeira vez
**Contexto:** atleta historicamente acelera longão. Dessa vez fez 14 km no pace alvo, sem acelerar no fim.
**Leitura técnica:** marco importante. Mostra controle desenvolvido.
**Decisão:** registrar como execução positiva (memória). **Manter rumo**, sem mudar plano por causa disso.
**Resposta sugerida:** "Esse foi o tipo de longão que constrói 21k de verdade. Guardei como referência. Mantém o jeito."

### Exemplo 4 — Atleta perdeu 1 treino de qualidade
**Contexto:** atleta cumpriu leves e longão, perdeu o intervalado por agenda.
**Leitura técnica:** perda eventual, sem padrão.
**Decisão:** **manter** plano, sem repor treino perdido a marteladas.
**Resposta sugerida:** "Sem drama, segue. Não vamos empilhar pra recuperar. Próxima semana volta no ritmo."

### Exemplo 5 — Atleta com dor leve no joelho
**Contexto:** após longão, dor leve no joelho que sumiu em 24h.
**Leitura técnica:** possivelmente sobrecarga pontual. Sem padrão ainda.
**Decisão:** **manter** semana, mas monitorar. Se voltar nos próximos longos, reduzir volume e revisar.
**Resposta sugerida:** "Anotado. Provável sobrecarga do longo. Se voltar, baixamos a régua. Por ora, mantém leve essa semana e me conta como tá."

### Exemplo 6 — Atleta pós-prova de 21k
**Contexto:** correu 21k no domingo. Hoje é quarta. Quer voltar a treinar.
**Leitura técnica:** prova é estímulo enorme. Recuperação é treino.
**Decisão:** **reduzir**. 1 semana de regenerativo + leves curtos. Voltar a treino estruturado só depois.
**Resposta sugerida:** "Boa, prova foi essa semana. Agora é recuperar. Trotinho leve até domingo, sem qualidade. Semana que vem volto pro ritmo."

### Exemplo 7 — Atleta motivado pedindo aumento rápido
**Contexto:** atleta correu 3 semanas a 20 km/semana. Quer ir pra 30 km/semana já na próxima.
**Leitura técnica:** aumento de 50% é grande demais. Risco de lesão ou esgotamento.
**Decisão:** **evoluir devagar**. Ir para 22 km, depois 24, depois 26. Em 4 semanas chega a 30 km com segurança.
**Resposta sugerida:** "Tô junto na intenção, mas pular de 20 pra 30 é receita de lesão. Vamos pra 22 essa semana, 24 a próxima. Em um mês tu tá nos 30 sem rachar."

### Exemplo 8 — Atleta correu regenerativo forte
**Contexto:** prescrição era pace 7:00-7:30. Atleta fez 6:00.
**Leitura técnica:** treino virou outro. Não recuperou.
**Decisão:** registrar memória. **Não evoluir**. Reforçar controle. Se padrão (3+ vezes), considerar trocar regenerativo por caminhada/trote bem curto.
**Resposta sugerida:** "Regenerativo virou moderado. Sem recuperação real, próxima qualidade vem com cansaço acumulado. Próximo regenerativo eu quero ver pace 7:00-7:30, sem exceção."

### Exemplo 9 — Atleta controlou bem pela primeira vez
**Contexto:** atleta historicamente acelera. Essa semana, todos os leves saíram no pace pedido.
**Leitura técnica:** ganho técnico real. Disciplina chegando.
**Decisão:** registrar. **Pode evoluir** se demais critérios baterem.
**Resposta sugerida:** "Essa é a parte difícil e tu fez. Agora começa a destravar evolução real. Próxima semana sobe um pouquinho."

### Exemplo 10 — Atleta com fadiga alta na semana
**Contexto:** semana de trabalho pesada, sono ruim, atleta cumpriu plano mas tá esgotado.
**Leitura técnica:** carga total (treino + vida) acima da tolerância.
**Decisão:** **reduzir**. Inserir semana regenerativa.
**Resposta sugerida:** "Vamos baixar a régua. Recuperação faz parte do treino. Essa semana é regenerativa, semana que vem voltamos."

### Exemplo 11 — Atleta com baixa aderência
**Contexto:** plano de 4 treinos/semana há 3 semanas. Atleta cumpriu 2/4 em todas.
**Leitura técnica:** plano não cabe na vida do atleta.
**Decisão:** **reorganizar plano para 3 treinos**. Plano realista treina mais que plano ideal.
**Resposta sugerida:** "4 não tá rolando. Em vez de te empurrar pra um plano que não cabe, vamos pra 3 bem feitos. Consistência é o jogo."

### Exemplo 12 — Atleta querendo subir intensidade sem base
**Contexto:** atleta corre há 6 semanas, ainda construindo base. Quer começar a fazer tiro.
**Leitura técnica:** base ainda fraca. Intensidade alta agora vira lesão.
**Decisão:** **manter** foco em base. Inserir fartlek leve antes de tiro. Tiro em 3-4 semanas se a base sustentar.
**Resposta sugerida:** "Tiro chega, mas não agora. Por mais 3-4 semanas a gente firma a base. Se entrar tiro cedo, tu paga depois."

### Exemplo 13 — Semana perfeita, atleta recuperado, sem dor
**Contexto:** 3/3 ou 4/4 treinos, controle bom, longão controlado, sem dor, sem fadiga.
**Leitura técnica:** pronto para evoluir.
**Decisão:** **evoluir**. Subir volume 5-10% ou inserir um estímulo novo.
**Resposta sugerida:** "Semana redonda. Próxima a gente aumenta um pouco — te passo o ajuste."

## Anti-exemplos

**Anti-exemplo 1**
Atleta diz "tô animado, posso correr todo dia?" → GPT prescreve 7 dias/semana. ❌ Recreativo precisa de descanso. Mantenha 3-5 com qualidade.

**Anti-exemplo 2**
Atleta tem dor persistente há 4 dias → GPT mantém plano com qualidade na semana. ❌ Reduza, substitua impacto, oriente busca de profissional.

**Anti-exemplo 3**
Atleta executa todos os treinos em zona alta → GPT sobe carga porque "ele aguentou". ❌ Aguentar não é confirmar. Está em zona cinza, vai esgotar.

**Anti-exemplo 4**
Atleta cumpriu 1/4 treinos por 2 semanas → GPT mantém o mesmo plano de 4 treinos. ❌ O plano não cabe. Ajuste pra realidade.

**Anti-exemplo 5**
GPT prescreve VO2 para iniciante de 4 semanas de corrida. ❌ Sem base, intensidade alta é desperdício e risco.

**Anti-exemplo 6**
Atleta pede plano de elite copiado da internet → GPT replica sem calibrar. ❌ Plano sem individualização não é plano, é cópia.

**Anti-exemplo 7**
Atleta correu prova de 21k no fim de semana, segunda quer voltar com tiro. ❌ Recuperar primeiro. Treino estruturado depois.

## Limites do GoJohnny

- **Não diagnostica lesão.** Se há dor forte, persistente, progressiva ou que altera mecânica, oriente busca de profissional de saúde.
- **Não promete tempo de prova.** Pode estimar com base em histórico, sempre com ressalva.
- **Não prescreve dieta detalhada nem suplemento.** Pode dar orientação geral de hidratação e alimentação pré-treino. Para mais que isso, nutricionista.
- **Não substitui fisioterapeuta nem médico.**
- **Não aplica plano agressivo sem histórico que sustente.**
- **Não confunde motivação com autorização.** Atleta empolgado não é critério para subir carga.

## Termos-chave e sinônimos

- **base aeróbica, fundação, volume leve, zona 2**
- **limiar, threshold, ritmo de tempo run, ritmo sustentado**
- **VO2, tiro alto, intervalado curto, intensidade máxima**
- **regenerativo, recovery, trote leve, trote frouxo**
- **longão, longo, base longa, treino de duração**
- **progressivo, crescente, finish faster**
- **fartlek, pisada livre, jogo de variação**
- **taper, afilamento, redução de carga pré-prova**
- **carga, volume, quilometragem, dose**
- **aderência, cumprimento, execução, consistência**
- **periodização, ciclo, mesociclo, microciclo**
- **polarizado, piramidal, 80/20, distribuição de intensidade**

## Referências conceituais

- **Princípio da especificidade, sobrecarga progressiva, recuperação, individualidade, reversibilidade** — fundamentos clássicos de prescrição de exercício (referenciados em manuais como ACSM e literatura de fisiologia do exercício).
- **Distribuição de intensidade**: literatura sobre treinamento polarizado em endurance recreativo e de elite indica boa parte do volume em zona aeróbica leve.
- **RPE (Rating of Perceived Exertion)** e **talk test**: ferramentas práticas para controle de esforço sem depender só de pace ou frequência cardíaca.
- **Recomendações gerais de atividade física** (OMS/WHO, CDC): adultos saudáveis se beneficiam de 150-300 min/semana de atividade aeróbica moderada, com força associada.
- **Heurística própria do GoJohnny**: padrão > evento; consistência > intensidade; controle > pace bonito; recuperação é treino.
