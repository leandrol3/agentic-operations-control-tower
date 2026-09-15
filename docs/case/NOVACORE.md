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
