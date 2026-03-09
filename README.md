# regeneracao
[furb] projeto de pesquisa - regeneração de vegetação

o script `extrator.py` automatiza a coleta de todas as 12 bandas espectrais da base de dados Sentinel-2 (S2_SR_HARMONIZED) para os polígonos/áreas cadastradas no diretório `areas`, com preenchimento de histórico retroativo e atualização semanal (por enquanto via GitHub Actions).

## rodando o projeto localmente
deve-se ter instalados em seu ambiente o Python, em versão 3.12 ou mais recente, Poetry (gerenciador de dependências). além disso, é necessário uma conta no Google Cloud Console para configurar a chave de acesso.

após instalação das dependências e configuração das variáveis de ambientes (cfe. `.env.example`), basta rodar o projeto através do poetry (`poetry run python extrator.py`)

### configurando o Google Cloud Console
visto que o script utiliza uma conta de serviço para rodar de forma "headless" (sem precisar abrir o navegador para logar), é necessário criar um projeto (dentro do Google Cloud Console), ativar a API ("APIs e Serviços" > "Biblioteca" > Google Earth Engine API), e, após isso, cadastrar uma conta de serviço ("IAM e Administrador" > "Contas de Serviço" > "+ Criar Conta de Serviço").

após isso, gere a chave JSON desta conta clicando no e-mail dela e indo na aba de "Chaves". selecione a opção JSON e baixe o arquivo. copie o conteúdo do mesmo e adicione como uma variável de ambiente local (cfe. arquivo `.env.example`)

## estrutura de pastas e arquivos
o script busca arquivos .shp recursivamente dentro do diretório `areas/`. o nome do arquivo define o código da área e a data de início da busca dos dados.

o arquivo deve seguir um padrão de nomeclatura do tipo `codigo-AAAAMMDD.ext`, onde o código pode ser alfanumérico, e a data deve estar exatamente conforme o padrão (ano, mês, dia, sem separação), como, por exemplo, `areas/10/10-20260101.shp`.

## output/saída de dados
o script gera um arquivo excel com o nome `analise.xlsx` (configurável por variável de ambiente). este arquivo conterá uma para cada código de área, onde conterá a data e todas as bandas presentes no dataset (B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B11, B12) para cada semana desde a primeira captura (definida no nome do arquivo).