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
  recursos produtivos são simplificados, sem restrição de capacidade horária ainda.
- Limites de política são inclusivos; custo acima de 100 mil requer gerente.
  Mesmo abaixo desse limite existe aprovação humana. A aplicação de políticas é exercício futuro.

## Alternativas para investigar, sem resposta pronta
A: esperar Alpha; B: comprar de Beta; C: transferir; D: transferir e replanejar.
Priorizar Atlas pode evitar multa relevante, mas afeta outros pedidos e estoque de segurança.
O start fornece evidências e cálculo de multa; não calcula cronograma nem escolhe o melhor plano.
