# NovaCore e premissas do digital twin
Empresa fictícia B2B: quatro fábricas, três CDs no contexto narrativo, fornecedores e clientes enterprise.
O recorte de dados modela as quatro fábricas; CDs não participam ainda deste incidente.
Antes: evento → pessoas → emails/planilhas → reuniões → decisão (horas, ilustrativo).
Depois: evento → investigação paralela → cenários → challenger → recomendação → decisão humana
(minutos, objetivo pedagógico, não benchmark). Métrica de negócio: Time-to-Decision.

## Unidades e restrições
- Dinheiro: BRL, Decimal, até duas casas. Margem é total do pedido; multa é BRL por dia de atraso,
  sem teto neste recorte. Dias corridos; datas fixas, sem dependência do relógio.
- Quantidade de produto × material_units_per_product = demanda de material.
- M42: demanda SP de 750, estoque físico 400, reservas externas de 100, disponível 300.
  Reservas não correspondem às três ordens exibidas e não podem ser reutilizadas.
- Safety stock é piso de planejamento, não reserva. Disponível pode incluir esse piso;
  transferível sem romper o piso subtrai também safety stock.
- Campinas: 500 disponíveis, só 300 transferíveis preservando safety stock. Transferir 450
  cobre o déficit de SP, mas deixa 50, abaixo do piso 200. Challenger deve discutir isso.
- Beta fornece até 450 unidades em dois dias, a R$145 versus Alpha R$100.
  Lead time de fornecedor é até SP, transporte incluído; não somar novamente frete de transferência.
- Alpha deveria entregar em 01/10; atraso de 7 dias desloca chegada para 08/10.
  lead_time_days do cadastro é prazo normal de nova compra, não somar ao atraso do incidente.
- Rotas são transferências entre plantas, custo fixo por viagem, capacidade por viagem.
  Não há calculadora de frete ou alocador automático no start.
- Para experimentos futuros: produção dura um dia e entrega ao cliente mais um dia;
  recursos produtivos são simplificados, sem restrição de capacidade horária ainda; veja a convenção abaixo.
- Limites de política são inclusivos; custo acima de 100 mil requer gerente.
  Mesmo abaixo desse limite existe aprovação humana. A aplicação de políticas será demonstrada na progressão futura.

## Alternativas para investigar, sem resposta pronta
A: esperar Alpha; B: comprar de Beta; C: transferir; D: transferir e replanejar.
Priorizar Atlas pode evitar multa relevante, mas afeta outros pedidos e estoque de segurança.
O start fornece evidências e cálculo de multa; não calcula cronograma nem escolhe o melhor plano.

## Ordens relacionadas não são impacto confirmado

`get_orders(material, plant)` seleciona ordens por material e planta; não aloca estoque nem calcula
atraso. A CLI chama esse resultado de `related_orders` e informa `impact_status: not_assessed`.
O déficit agregado de 450 unidades não prova que as três ordens atrasarão. As 300 unidades locais
podem atender integralmente PO-001, dependendo da alocação. Confirmar impacto exige um cenário,
alocação e calendário de produção/entrega. O start não realiza essa simulação.

## Convenção temporal do case

- Datas ISO representam dias civis de São Paulo (`America/Sao_Paulo`), sem horas nem conversão UTC.
  Finais de semana e feriados contam. Não usar a data atual do computador.
- D0 = início de 2026-10-01: estoque é o snapshot disponível antes de movimentações; Alpha era
  esperado nesse dia e passa a ser esperado no início de 2026-10-08 (D0 + 7).
- Lead time N: partida/pedido no início de D, material utilizável no início de D + N.
  Beta pedido em 01/10 chega em 03/10; transferência expressa iniciada em 01/10 chega em 02/10.
- `production_date` é o dia planejado da produção: inicia de manhã e conclui ao final do mesmo dia.
  Material deve estar disponível no início desse dia. O transporte ao cliente ocupa o dia seguinte,
  com entrega ao final desse dia. Assim, produção em 02/10 permite entrega em 03/10.
- `delivery_date` é o prazo ao final do dia. Atraso = max(0, data efetiva de entrega − delivery_date),
  em dias. Entrega no dia do prazo tem atraso zero. CO-001 entregue em 04/10 tem um dia de atraso.
- Sem antecipação, a primeira entrega possível de uma ordem isolada é
  max(production_date, chegada do material) + 1 dia. Isso é uma convenção para futura simulação,
  não um plano: pressupõe material suficiente e desconsidera competição entre ordens.
- Sete dias de atraso de Alpha não equivalem a sete dias de atraso de cada cliente.
  `calculate_penalty('CO-001', 7)` recebe atraso hipotético já calculado, não o atraso do fornecedor.

## Simulação implementada no candidato complete

As tools de consulta continuam retornando relações. Somente `run INCIDENT-001` simula impacto **por
cenário**, ainda sem afirmar impacto ocorrido no mundo real. Nenhum dado de estoque é alterado.

### Alocação e custos

- Em todos os cenários: ordenar por prioridade estratégica, prazo do cliente e ID; material por
  data de disponibilidade. Cada unidade é consumida uma única vez; reservas externas são excluídas.
- Lotes produtivos indivisíveis; sem produção antecipada ou entrega parcial. A mesma fábrica pode
  processar mais de uma ordem no mesmo dia: capacidade horária ainda não modelada.
- A usa 300 locais e espera 450 de Alpha; B substitui essas 450 por Beta;
  C transfere 450 por expresso; D transfere 300 por rota padrão (piso de Campinas preservado),
  replaneja PO-002 para 04/10 e espera 150 de Alpha para completar PO-003.
- A quantidade da compra original de Alpha não consta dos dados. Assume-se disponibilidade para
  o residual no novo prazo, limitada pela capacidade cadastrada. Challenger exige confirmação humana.
- Custo total **incremental** = prêmio de material alternativo + frete de transferência + multas.
  O material base já comprometido, custo de reposição de Campinas e eventual cancelamento de Alpha
  não entram. B cobra `(145 − 100) × 450`, não `145 × 450`; frete de Beta já está no lead time/preço.
- Capacidade de transporte vale para uma viagem. O simulador bloqueia se a transferência exceder
  estoque ou capacidade; não inventa viagens extras. Se não consegue avaliar A–D, bloqueia a recomendação.
- Regra conservadora do case: não recomendar transferência que rompa o piso de Campinas. Consumo
  do safety stock local é permitido sob hipótese de reposição a revisar. Essa assimetria é explícita;
  não é uma regra universal de gestão de estoque. Challenger mostra a violação de C (150 unidades).
- Entre cenários admissíveis, minimizar custo incremental total; empate por ID. Atraso estratégico
  deve respeitar a política. Frete expresso acima do limite bloqueia o cenário. Custo acima do limiar
  exige gerente; abaixo dele também há aprovação por responsável de operações.

| Cenário | Prêmio material | Frete | Multas | Total BRL | Atrasos CO-001/002/003 |
|---|---:|---:|---:|---:|---|
| A | 0 | 0 | 23.500 | 23.500 | 0 / 4 / 3 dias |
| B | 20.250 | 0 | 0 | 20.250 | 0 / 0 / 0 dias |
| C | 0 | 18.000 | 0 | 18.000 | 0 / 0 / 0 dias; piso violado |
| D | 0 | 5.000 | 7.500 | 12.500 | 0 / 0 / 3 dias |

D é recomendado **sob essas premissas e esse objetivo econômico**. B evita todo atraso com custo maior;
essa diferença sustenta a discussão. Não existe alegação de plano ótimo fora dos quatro cenários.
`avoided_penalty_brl = 23.500 − 7.500 = 16.000`; economia total versus A é 11.000, um conceito diferente.
`customer_delay_days` é o maior atraso entre os clientes no cenário selecionado (3), não o atraso
estratégico (0). `confidence=0.65` é marcador conservador do mock, não probabilidade calibrada.

A recomendação termina em `awaiting_approval`, com solicitações de confirmação humana. Não existe
comando de aprovar, integração de aprovação, retomada ou ação operacional nesta aula. A duração da CLI
mede o workflow até a recomendação, não o Time-to-Decision completo, pois a decisão humana está pendente.
