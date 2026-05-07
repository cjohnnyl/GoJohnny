# Tipos de Treino do GoJohnny

## Objetivo do arquivo

Manual completo dos tipos de treino que o GoJohnny pode prescrever, analisar e adaptar. Para cada tipo: objetivo, quando usar, intensidade esperada, sensação esperada, exemplo, erro comum, como saber se foi bem executado, quando evitar e como o GoJohnny deve responder após a execução.

Este arquivo é o vocabulário técnico do treinador. Sem ele, o GoJohnny prescreve e analisa no escuro.

## Quando o GPT deve consultar este arquivo

- Ao prescrever um treino e precisar definir intensidade, instrução e sensação alvo.
- Ao analisar um treino executado e julgar se foi bem feito.
- Ao explicar para o atleta o objetivo de um treino.
- Ao decidir substituir um tipo de treino por outro (ex.: trocar tiro por fartlek).
- Quando o atleta confunde tipos ("achei que regenerativo era pra correr forte").
- Para identificar erro comum em um relato pós-treino.

## Quando este arquivo NÃO deve ser usado como fonte principal

- Para decidir **estrutura semanal** ou **distribuição de intensidade**. Use `metodologia_corrida.md`.
- Para decidir **o que salvar** sobre o treino executado. Use `memoria.md`.
- Para consultar **plano vigente do atleta**. Use a API.

## Relação com a API

A API guarda o que foi prescrito e o que foi executado para cada atleta. Este arquivo fornece os **critérios técnicos** para preencher essa prescrição com sentido — definir intensidade, instrução, sensação alvo — e para ler a execução de volta com profundidade.

## Princípios centrais

1. **Cada treino tem propósito.** Sem propósito, é só correr.
2. **Intensidade prescrita ≠ intensidade executada.** O treinador analisa o gap.
3. **Sensação importa tanto quanto pace.** RPE e talk test são dado válido.
4. **Erro de execução é dado, não falha moral.** Use para calibrar, não para repreender.
5. **Treino bem feito é treino que cumpre o objetivo, não o que tem pace bonito.**
6. **Tipo de treino só faz sentido na semana certa, no atleta certo, no momento certo.**

## Regras práticas

- Sempre comunique ao atleta o **objetivo** do treino, não só os números.
- Sempre indique a **sensação esperada**, não só o pace.
- Use **RPE 1-10** ou **talk test** como apoio quando pace não estiver disponível ou for variável (calor, terreno).
- Em prescrições, dê **faixa de pace**, não pace exato (ex.: 6:00-6:20).
- Após execução, julgue pelo **objetivo cumprido**, não por estética de número.

## Tabela resumida dos tipos de treino

| Tipo | Objetivo | Intensidade | Sensação | Erro comum | Quando evitar |
|---|---|---|---|---|---|
| Regenerativo | Recuperar | Muito leve (RPE 2-3) | Conversa fácil, pernas leves | Acelerar | Quando confunde com leve |
| Leve | Construir base | Leve (RPE 3-4) | Conversa possível | Virar moderado | Após dia muito forte |
| Base aeróbica | Volume aeróbico | Leve a leve+ (RPE 3-5) | Confortável, sustentável | Ficar em zona cinza | — |
| Longo | Resistência | Leve a moderado controlado (RPE 4-5) | Sustentável até o fim | Virar progressivo sem propósito | Pós-prova, com dor, com fadiga alta |
| Longo controlado | Controle + resistência | Leve controlado (RPE 4) | Disciplina | Acelerar no fim | Atleta sem controle de ritmo ainda |
| Progressivo | Controle + crescer ritmo | Leve → moderado/forte controlado (RPE 3→7) | Crescente | Começar forte | Em fase de base inicial |
| Moderado controlado | Sustentação de ritmo | Moderado (RPE 5-6) | Firme, mas sustentável | Virar forte | Sem base; dia pós-qualidade |
| Fartlek | Variação livre de ritmo | Variável (RPE 4-8) | Brincado, variado | Virar tiro disfarçado | Com dor; sem aquecimento |
| Intervalado / tiro | Estímulo intenso | Forte (RPE 8-9) | Curto, intenso, recuperação real | Sem aquecer; sem recuperar | Iniciante sem base; dor; fadiga alta |
| Tempo run | Sustentar limiar | Moderado-forte (RPE 7) | Confortavelmente difícil | Fazer como tiro | Sem base; após qualidade no dia anterior |
| Limiar | Limiar | Forte controlado (RPE 7-8) | Concentração alta | Virar VO2 | Sem base aeróbica sólida |
| VO2 | Capacidade máxima | Muito forte (RPE 9) | Curto, próximo do máximo | Aplicar sem base | Iniciante; dor; fadiga; após prova |
| Subida | Força específica | Moderado-forte (RPE 6-8) | Pernas pesadas | Atacar demais sem técnica | Dor em panturrilha/aquiles/joelho |
| Ritmo de prova | Específico | Conforme prova (RPE 6-8) | Como na prova | Antecipar demais no ciclo | Início de ciclo |
| Teste controlado | Calibração | Variável conforme teste | Esforço calibrado | Improvisar protocolo | Em fadiga ou dor |
| Semana regenerativa | Consolidar adaptação | Toda a semana mais leve | Recuperação | Continuar com qualidade | — |
| Taper | Pré-prova | Volume reduzido, alguma intensidade | Energia retornando | Cortar tudo ou treinar forte | Não evitar; aplicar sempre antes de prova alvo |
| Treino livre controlado | Liberdade com limites | Variável (RPE até 6) | Prazer + responsabilidade | Virar competição | Em fadiga ou dor |

## Detalhamento por tipo de treino

### 1. Regenerativo

**Objetivo:** recuperação ativa. Soltar pernas, aumentar circulação, acelerar recuperação entre treinos.

**Quando usar:** dia seguinte a treino forte ou longo. Início de semana após prova. Como "ponte" entre dois estímulos importantes.

**Intensidade:** muito leve. RPE 2-3. Pace bem abaixo do pace de leve do atleta. Frequência cardíaca baixa.

**Sensação:** "podia conversar tranquilo o tempo todo", pernas leves, não cansa. Termina como começou ou melhor.

**Exemplo prático:** 4-5 km em pace 7:00-7:30 (para um atleta cujo leve é 6:00).

**Erro comum:** transformar em moderado. Pace cai pra 5:50, 6:00 e o treino vira outro. Não recupera nada.

**Como saber se foi bem executado:**
- Pace dentro da faixa pedida.
- RPE baixo durante todo treino.
- Sensação de pernas mais leves no fim.
- Sem ofegar.

**Quando evitar:** se o atleta sistematicamente não consegue controlar e o treino vira moderado, considere trocar por **caminhada** ou **off** até desenvolver controle.

**Como o GoJohnny responde após execução:**
- **Bem feito:** "Boa, regenerativo de verdade. Pernas vão te agradecer."
- **Mal feito (forte):** "Regenerativo é regenerativo, não é treino de ego. Próximo eu quero ver pace dentro da faixa."
- **Padrão:** se já se repetiu, registrar erro_recorrente e calibrar.

---

### 2. Leve

**Objetivo:** construir base aeróbica sustentável, somar volume sem desgaste alto.

**Quando usar:** maior parte da semana de qualquer corredor. É o "pão com manteiga" do treino.

**Intensidade:** leve. RPE 3-4. Conversa possível com frases médias.

**Sensação:** confortável, "podia continuar". Não cansa demais. Termina sem grande desgaste.

**Exemplo prático:** 5-7 km em pace de leve do atleta.

**Erro comum:** virar moderado por conta de empolgação ou competitividade interna.

**Como saber se foi bem executado:**
- Pace dentro da faixa.
- Sem grande cansaço no fim.
- Atleta termina sentindo que poderia ter feito mais — e não fez por disciplina.

**Quando evitar:** após dia muito forte; substituir por regenerativo.

**Resposta após execução:**
- **Bem feito:** "Boa, esse tijolinho é o que constrói base."
- **Forte demais:** "Saiu mais firme que o pedido. Próximo eu quero pace X-Y."

---

### 3. Base aeróbica

**Objetivo:** desenvolver capacidade aeróbica geral. Pode ter volume um pouco maior que o leve comum, ainda em intensidade controlada.

**Quando usar:** semanas de construção. Atletas em fase inicial ou retornando.

**Intensidade:** leve a leve+. RPE 3-5.

**Sensação:** sustentável. Ao fim, atleta sente que treinou, mas sem desgaste.

**Exemplo prático:** 8-10 km em pace de leve, com possível leve crescimento natural no meio sem virar progressivo.

**Erro comum:** ficar em zona cinza moderada o tempo todo, achando que está em base.

**Como saber se foi bem executado:**
- Maior parte do treino em RPE 3-4.
- Pace dentro da faixa, com leve oscilação natural.

**Resposta:** "Volume bem feito, é assim que se constrói."

---

### 4. Longo

**Objetivo:** desenvolver resistência aeróbica e capacidade de tempo em pé.

**Quando usar:** uma vez por semana, no dia de maior disponibilidade. Ciclo inteiro para meia e maratona.

**Intensidade:** leve a moderado controlado. RPE 4-5. Faixa de pace mais lenta que pace de prova de 21k.

**Sensação:** sustentável. Atleta deve terminar com sensação de "fiz, mas não me destruí". Cansaço de pernas, sim. Esgotamento, não.

**Exemplo prático:** 12-16 km para um corredor de 21k em fase intermediária. Pace 30-60 segundos mais lento que pace alvo de prova.

**Erro comum:** transformar em prova. Acelerar no final sem ser pedido. Buscar pace bonito no Strava.

**Como saber se foi bem executado:**
- Pace dentro da faixa do início ao fim.
- Atleta consegue continuar mais 1-2 km se necessário.
- Sem dor.
- Recuperação no dia seguinte é boa.

**Quando evitar:** pós-prova recente, com dor, com fadiga alta, sem ter feito leves antes.

**Resposta:**
- **Bem feito:** "Esse é o longão que constrói 21k. Manda o próximo igual."
- **Acelerou no fim:** "Distância feita, mas longão não é lugar pra provar nada. Próximo, controle até o fim."

---

### 5. Longo controlado

**Objetivo:** trabalhar disciplina de pace em treino longo. Útil para atleta que tem dificuldade de controle.

**Quando usar:** quando atleta historicamente acelera longão. Em fase em que controle é prioridade.

**Intensidade:** leve controlado. RPE 4. Pace fixo, sem variação.

**Sensação:** "tenho que segurar". Treino mental tanto quanto físico.

**Exemplo prático:** 14 km em pace alvo de 6:30-6:40, sem deixar passar nem em descida.

**Erro comum:** acelerar no fim. Subir pace por causa de outro corredor passando.

**Como saber se foi bem executado:**
- Variação de pace mínima do início ao fim.
- Atleta termina relatando "deu vontade de acelerar e segurei".

**Resposta:**
- **Bem feito:** "Esse foi o tipo de execução que destrava 21k. Disciplina é treino também."

---

### 6. Progressivo

**Objetivo:** ensinar controle de ritmo crescente. Trabalha capacidade de "fechar forte" sem queimar.

**Quando usar:** fase intermediária e específica. Não em base inicial.

**Intensidade:** começa em leve (RPE 3) e termina moderado a forte controlado (RPE 6-7).

**Sensação:** começa fácil, fica firme, termina desafiador mas controlado.

**Exemplo prático:** 9 km divididos em 3 partes: 3 km pace 6:30, 3 km pace 6:00, 3 km pace 5:40.

**Erro comum:** começar forte demais e não conseguir progredir. Ou virar tiro disfarçado no terço final.

**Como saber se foi bem executado:**
- Cada bloco está mais rápido que o anterior.
- Atleta termina com a sensação de "mais um pouco eu seguraria".
- Sem ofegar descontrolado no fim.

**Quando evitar:** em fase de base inicial; sem aquecimento adequado; com fadiga.

**Resposta:**
- **Bem feito:** "Progressivo de verdade. Esse trabalho ensina prova."

---

### 7. Moderado controlado

**Objetivo:** sustentação de ritmo entre leve e limiar. Trabalha percepção e tolerância sem chegar ao desgaste do limiar.

**Quando usar:** semanas em que se quer estímulo médio sem qualidade pesada.

**Intensidade:** moderada. RPE 5-6.

**Sensação:** firme mas sustentável. "Conversa em frases curtas".

**Exemplo prático:** 6 km em pace 30 segundos mais rápido que leve, mantido constante.

**Erro comum:** virar forte. Confundir moderado com limiar.

**Resposta:** "Bom, ritmo firme e controlado. É essa percepção que afina pra prova."

---

### 8. Fartlek

**Objetivo:** variar ritmo de forma não-estruturada. Quebrar monotonia. Estimular múltiplos sistemas.

**Quando usar:** semanas que pedem qualidade leve. Atletas iniciantes que ainda não estão prontos para tiro estruturado.

**Intensidade:** variável. RPE 4-8 conforme blocos.

**Sensação:** brincada, lúdica. "Acelera quando passa um cachorro" estilo livre, ou estruturado por tempo.

**Exemplo prático:** 30 minutos com aquecimento de 10 min + 10 blocos de 1 min forte / 1 min leve + 5 min volta à calma.

**Erro comum:** virar tiro alto disfarçado. Forte demais, recuperação curta demais.

**Como saber se foi bem executado:**
- Variação real entre blocos.
- Atleta termina cansado, mas não destruído.

**Quando evitar:** com dor, sem aquecimento, em pós-prova recente.

**Resposta:** "Boa, fartlek bem dosado. Esse é o tipo de qualidade que cabe sem te quebrar."

---

### 9. Intervalado / tiro

**Objetivo:** estímulo intenso curto. Desenvolver capacidade anaeróbica e VO2.

**Quando usar:** atleta com base sólida, em fase específica para 5k ou 10k. Atletas de 21k em momentos pontuais do ciclo.

**Intensidade:** forte. RPE 8-9.

**Sensação:** intensa, curta, recuperação real entre tiros.

**Exemplo prático:** 8x 400 m em ritmo forte, com 1-2 min de trote leve entre cada. Aquecimento e volta à calma sempre.

**Erro comum:**
- Pular aquecimento.
- Pular volta à calma.
- Recuperação curta demais entre tiros.
- Tiros desiguais (primeiros muito fortes, últimos arrastados).

**Como saber se foi bem executado:**
- Tempos consistentes entre tiros (variação ≤2-3 segundos).
- Atleta cumpre todos os tiros sem cair de produção.
- Recuperação entre tiros foi suficiente.

**Quando evitar:**
- Iniciante absoluto sem base.
- Com dor.
- Com fadiga alta.
- Em semana pós-prova.
- Como primeiro estímulo em retomada.

**Resposta:**
- **Bem feito (consistente):** "Tiros consistentes, esse é o sinal. Aquecimento e volta à calma fizeram diferença."
- **Mal feito (decaindo):** "Os primeiros foram fortes demais e os últimos pagaram. Próximo, ritmo controlado já no primeiro tiro."

---

### 10. Tempo run

**Objetivo:** sustentar ritmo próximo ao limiar por tempo prolongado.

**Quando usar:** fase específica para 10k e 21k, com base estabelecida.

**Intensidade:** moderado-forte. RPE 7. "Confortavelmente difícil".

**Sensação:** atleta consegue manter, mas precisa concentração. Fala em frases muito curtas ou monossílabos.

**Exemplo prático:** 20 minutos em pace de tempo (próximo ao pace de prova de 10k), entre aquecimento e volta à calma.

**Erro comum:** transformar em tiro. Ir forte demais e ter que reduzir antes do fim.

**Como saber se foi bem executado:**
- Pace estável durante todo o bloco.
- Atleta termina o bloco no pace alvo, sem ter quebrado.

**Quando evitar:** sem base aeróbica sólida; após qualidade no dia anterior.

**Resposta:** "Tempo run bem feito é treino que ensina a prova. Boa concentração."

---

### 11. Limiar

**Objetivo:** trabalhar limiar anaeróbico. Empurrar a fronteira de ritmo sustentável.

**Quando usar:** fase específica, com base sólida.

**Intensidade:** forte controlado. RPE 7-8. Em torno do pace de prova de 10k para corredor recreativo.

**Sensação:** difícil mas controlado. Mais intenso que tempo run, mais sustentável que VO2.

**Exemplo prático:** 2 blocos de 10 minutos com 3 minutos de trote leve entre eles.

**Erro comum:** virar VO2. Confundir limiar com tiro.

**Quando evitar:** sem base aeróbica; com fadiga; iniciante.

**Resposta:** "Limiar bem dosado. Sente onde fica firme e sustentável."

---

### 12. VO2

**Objetivo:** desenvolver capacidade máxima aeróbica.

**Quando usar:** atleta com base sólida, em fase específica para distâncias curtas. Para 21k, usar com parcimônia.

**Intensidade:** muito forte. RPE 9. Próximo do máximo sustentável por 6-8 minutos.

**Sensação:** muito intenso. Sem espaço para conversa.

**Exemplo prático:** 5x 800 m em ritmo de prova de 3k-5k, com recuperação ativa de 2-3 min entre cada.

**Erro comum:** aplicar sem base. Recuperação curta demais. Virar primeiro estímulo de uma retomada.

**Como saber se foi bem executado:**
- Cumpriu todos os blocos no pace alvo.
- Recuperação suficiente entre blocos.
- Sem dor.

**Quando evitar:**
- Iniciante.
- Sem base aeróbica.
- Com qualquer dor.
- Em fadiga alta.
- Após prova recente.

**Resposta:** "VO2 bem feito é raro e valioso. Mas é estímulo forte — descanso amanhã."

---

### 13. Subida

**Objetivo:** força específica de corrida. Técnica. Estímulo cardiovascular alto sem velocidade horizontal.

**Quando usar:** uma vez por semana ou a cada 10-14 dias. Boa alternativa a tiro em piso plano para variação.

**Intensidade:** moderado-forte. RPE 6-8 conforme inclinação e duração.

**Sensação:** pernas pesadas. Cardio alto. Foco em postura e cadência.

**Exemplo prático:** 8x subidas de 30-45 segundos em ladeira moderada (4-6%), trote leve para descer e recuperar.

**Erro comum:**
- Atacar a subida com técnica ruim (pisada longa, tronco caído).
- Não respeitar recuperação na descida.
- Fazer com dor em panturrilha, aquiles, joelho ou tibial.

**Como saber se foi bem executado:**
- Postura mantida do início ao fim.
- Tempos das subidas consistentes.
- Sem dor.

**Quando evitar:** dor em panturrilha, aquiles, joelho ou tornozelo. Iniciante absoluto sem nenhuma base.

**Resposta:** "Subida bem feita constrói força que tu sente em qualquer prova."

---

### 14. Ritmo de prova

**Objetivo:** ensaiar a sensação e o pace da prova alvo.

**Quando usar:** semanas-chave do ciclo, próximas à prova. Tipicamente nas últimas 4-6 semanas.

**Intensidade:** depende da prova. Para 21k recreativo, RPE 6-7.

**Sensação:** "isso é o que vou sentir no dia". Controle de pace é o foco.

**Exemplo prático:** 2 blocos de 15 minutos no pace alvo de 21k, com 5 min de trote entre eles. Total 35-40 min.

**Erro comum:**
- Antecipar no ciclo (fazer ritmo de prova em fase de base).
- Ir mais rápido que o alvo "porque tava bom".

**Como saber se foi bem executado:**
- Pace exatamente no alvo durante os blocos.
- Sensação de "consigo manter por 21k".

**Quando evitar:** início de ciclo; sem base; com dor.

**Resposta:** "Esse é o pace que vai te levar. Sentir ele agora é meio caminho andado."

---

### 15. Teste controlado

**Objetivo:** calibrar zonas, paces e capacidade atual do atleta.

**Quando usar:**
- Início de ciclo para definir paces.
- A cada 6-8 semanas para reavaliar.
- Quando dados parecem desatualizados.

**Intensidade:** depende do teste. Pode ser tempo run de 20 minutos, 5k cronometrado, ou 1.5k em ritmo forte.

**Sensação:** esforço calibrado para o protocolo escolhido.

**Exemplo prático:** 3k cronometrado em ritmo "o mais forte que sustenta", com aquecimento e volta à calma adequados.

**Erro comum:** improvisar protocolo. Aplicar sem aquecimento.

**Quando evitar:** em fadiga, dor, ou pós-prova recente.

**Resposta:** "Teste feito, agora a gente tem dado novo pra calibrar tudo."

---

### 16. Semana regenerativa

**Objetivo:** consolidar adaptação. Reduzir carga total para que o corpo absorva o trabalho das semanas anteriores.

**Quando usar:**
- A cada 3-4 semanas de carga.
- Pós-prova.
- Após bloco forte.
- Quando atleta acumula fadiga.

**Estrutura típica:** mesma frequência de treinos, mas com volume reduzido em ~30-40% e intensidade rebaixada (sem qualidade ou com qualidade leve).

**Erro comum:** continuar com qualidade pesada. Não reduzir volume. Achar que regenerativa é "fraqueza".

**Resposta:** "Semana regenerativa é onde a adaptação acontece. Treinar menos, agora, te deixa mais forte depois."

---

### 17. Taper

**Objetivo:** chegar à prova fresco, sem perder forma.

**Quando usar:** 2 semanas antes da prova alvo (10k, 21k). Para 42k, 2-3 semanas.

**Estrutura típica:**
- **Semana -2:** volume reduzido em ~30%. Manter alguma intensidade (curta).
- **Semana -1:** volume reduzido em ~50-60%. Treinos curtos em ritmo de prova ou leve. Último treino qualidade 4-5 dias antes da prova.
- **Últimos 2 dias:** muito leve ou off.

**Erro comum:**
- Cortar tudo (zera intensidade e atleta chega "desligado").
- Continuar treinando forte (chega cansado).
- Testar coisas novas (tênis novo, gel novo, prova-piloto).

**Como saber se foi bem executado:**
- Atleta chega na semana da prova com pernas leves e cabeça boa.
- Sem fadiga acumulada.

**Resposta:** "Taper é confiança no trabalho já feito. Menos volume, mesma cabeça."

---

### 18. Treino livre controlado

**Objetivo:** dar espaço para o atleta correr por prazer, mantendo limites.

**Quando usar:** dia em que o atleta quer correr "livre". Para evitar sair forte demais ou substituir um treino estruturado por bagunça.

**Intensidade:** variável, mas com teto. RPE até 6.

**Sensação:** prazer, sem competição, sem cobrança de pace.

**Exemplo prático:** "Corre 6-8 km hoje, no pace que te der vontade, mas sem ultrapassar moderado. Sem qualidade. Pode parar antes se quiser."

**Erro comum:** virar prova com amigo. Forçar pace.

**Resposta:** "Boa, esse é o tipo de treino que mantém a chama acesa. Sem perder a régua."

## Matriz: como o GoJohnny analisa qualquer treino

| Sinal na execução | Interpretação | Ação |
|---|---|---|
| Pace dentro do alvo, sem dor, RPE coerente | Treino bem executado | Reforçar, manter rumo |
| Pace mais rápido que alvo | Atleta perdeu controle | Registrar; se 1ª vez, observar; se padrão, ajustar |
| Pace mais lento que alvo | Pode ser fadiga, calor, desânimo | Investigar, não recriminar |
| RPE muito alto para pace baixo | Cansaço acumulado, calor, sono ruim | Considerar redução de carga |
| Variação grande dentro do bloco (em qualidade) | Distribuição ruim do esforço | Trabalhar percepção e cadência |
| Atleta ofegando muito em treino que não pedia | Treino virou outro | Ajustar instrução próxima vez |
| Dor após treino | Sinal de alerta | Reduzir, monitorar, profissional se persistir |
| Atleta consegue manter conversa em treino que pedia esforço | Não está estimulando | Subir um pouco a régua |

## Exemplos de análise pós-treino

### Exemplo 1
**Usuário diz:** "Era regenerativo, mas fiz pace 5:48."
**Interpretação:** saiu forte demais. Treino virou moderado.
**Ação:** salvar memória (1ª vez: feedback_treino; recorrente: erro_recorrente). Não recompensar com mais carga.
**Resposta sugerida:** "Boa, treino feito, mas regenerativo virou moderado. O ganho aqui agora é disciplina. Próximo eu quero ver pace mais frouxo."

### Exemplo 2
**Usuário diz:** "Fiz o longo inteiro constante, sem acelerar no final."
**Interpretação:** execução excelente. Controle desenvolvido.
**Ação:** registrar como execução positiva. Manter rumo.
**Resposta sugerida:** "Esse foi o tipo de execução que constrói 21k. Guardei como referência."

### Exemplo 3
**Usuário diz:** "Cumpri os 8x 400 m, mas o último tava bem mais lento que o primeiro."
**Interpretação:** distribuição ruim. Começou forte demais.
**Ação:** registrar. Reforçar pacing.
**Resposta sugerida:** "Tiros consistentes valem mais que tiro inicial bonito. Próxima vez, controla o primeiro pra fechar igual no último."

### Exemplo 4
**Usuário diz:** "Tempo run virou prova, fui mais forte que o alvo."
**Interpretação:** confundiu tempo com tiro.
**Ação:** explicar a diferença. Calibrar próxima prescrição.
**Resposta sugerida:** "Tempo run não é pra dar tudo. É confortavelmente difícil. Próximo, fica no pace alvo — ele que te ensina prova."

### Exemplo 5
**Usuário diz:** "Senti uma dor leve no joelho durante a subida."
**Interpretação:** sinal de alerta. Subida pode estar pedindo demais.
**Ação:** registrar lesao_dor. Reduzir/substituir próximo treino de impacto. Avaliar técnica e tênis.
**Resposta sugerida:** "Anotado. Próxima semana cortamos subida. Se a dor voltar em piso plano também, busca um profissional."

### Exemplo 6
**Usuário diz:** "Fiz o fartlek mas achei que dei tudo nos blocos fortes."
**Interpretação:** virou tiro disfarçado.
**Ação:** ajustar percepção. Fartlek é variação, não competição.
**Resposta sugerida:** "Fartlek não é máximo, é variação. Forte ali é firme, não 'dar tudo'. Próximo bloco forte é RPE 7, não 9."

### Exemplo 7
**Usuário diz:** "O leve de hoje tava difícil, RPE 6 pra um pace que normalmente é fácil."
**Interpretação:** fadiga acumulada, calor, sono ruim ou outro fator.
**Ação:** investigar antes de mudar plano. Se padrão, reduzir carga.
**Resposta sugerida:** "Como tá o sono e a semana? Pace de leve com RPE 6 é sinal de carga acumulada. Vamos ver se ajusta."

### Exemplo 8
**Usuário diz:** "Cumpri o longão sem dor e sobrou energia no fim."
**Interpretação:** execução boa, possível espaço para evoluir.
**Ação:** considerar leve aumento de volume na próxima semana.
**Resposta sugerida:** "Esse é sinal de que tá pronto pra um pouquinho mais. Próximo longão a gente sobe um trecho."

## Anti-exemplos

**Anti-exemplo 1**
GPT prescreve 12x 400 m forte para iniciante de 4 semanas. ❌ Sem base, intensidade alta vira lesão.

**Anti-exemplo 2**
Atleta termina longão em pace de prova → GPT elogia como "evolução". ❌ Longão não é prova. Reforça o controle, não o pace.

**Anti-exemplo 3**
Atleta com dor no joelho pede tiro → GPT prescreve mesmo assim. ❌ Dor muda a prioridade.

**Anti-exemplo 4**
GPT marca taper com volume igual ao da fase de carga. ❌ Taper sem redução não é taper.

**Anti-exemplo 5**
GPT prescreve VO2 dia seguinte ao tempo run. ❌ Dois estímulos pesados em sequência sem recuperação.

**Anti-exemplo 6**
GPT chama todo treino qualidade de "tiro". ❌ Tiro, fartlek, limiar, tempo run e VO2 são coisas diferentes. Vocabulário importa.

## Termos-chave e sinônimos

- **regenerativo, recovery, trote frouxo, soltinha**
- **leve, easy, base, trote**
- **base aeróbica, fundação, volume aeróbico**
- **longo, longão, base longa**
- **progressivo, crescente, finish faster, build-up**
- **moderado, ritmo firme, sub-limiar**
- **fartlek, brincadeira sueca, variação**
- **intervalado, tiro, repetição, série**
- **tempo run, tempo, ritmo de tempo, threshold pace**
- **limiar, threshold, T-pace**
- **VO2, V̇O₂max, intensidade alta**
- **subida, hill, ladeira, repetição em subida**
- **ritmo de prova, race pace, marathon pace, half pace**
- **teste, time trial, avaliação**
- **regenerativa, deload, semana de descarga**
- **taper, afilamento, pré-prova**
- **livre controlado, easy run, run by feel**

## Referências conceituais

- **Zonas de intensidade** (zona 1-5 ou variação por modelo): base de qualquer prescrição de endurance.
- **RPE 1-10** (Rating of Perceived Exertion) e **talk test**: ferramentas de campo para validar intensidade.
- **Princípio de variação de estímulos**: combinar leve, longo, limiar e intensidade alta produz adaptações mais completas que qualquer estímulo isolado.
- **Periodização**: organizar treinos ao longo de mesociclos (geral → específico → taper) é fundamento clássico de planejamento esportivo.
- **Princípio da recuperação entre estímulos altos**: 48-72h entre treinos de qualidade pesada é referência prática para a maior parte dos recreativos.
- **Heurística própria do GoJohnny**: cada treino tem propósito; o objetivo manda mais que o pace bonito; sensação é dado válido; padrão > evento.
