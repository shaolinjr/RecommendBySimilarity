
# coding: utf-8

import pandas as pd
import pprint
import numpy as np
import collections

# In[2]:

#Passos:
#1) Criar um df com os dados categoricos processados (pegar codigo no drive)
#2) Separar conjunto de treino e de teste
#3) Implementar algoritmo de rankeamento para cálculo de probabilidade
#4) Filtrar saídas do algoritmo de rankeamento
#5) Mostrar para o usuário os resultados filtrados com as taxas de recomendação

# Parte 2:
# No B4i temos que ter alguma forma do usuário que solicita o match avaliar a recomendação, com esses novos dados
# conseguimos usar os algoritmos de classificação e tornar a recomendação ainda mais precisa, da mesma forma que o
# Netflix começou a adotar!


# In[3]:
class Ranking (object):
    df = pd.DataFrame()
    
    def __init__(self,df, file_type="json"):
        self.df = df
        self.file_type = file_type


# 1) Criar um df com os dados categoricos processados (Nesse caso importamos os df's)

#Importando DataFrame Processado
df = pd.read_csv('data_processed.csv', sep=';')

# importar df que possui os dados categoricos e criar coluna de id
df_categ = pd.read_csv('dados.csv', sep=";")

#Criando coluna de id para futura visualização dos dados
df_categ['user_id'] = range(0,len(df_categ))
df['user_id']       = range(0,len(df))

# Reordenando as colunas do df do pandas
df_categ = df_categ[['user_id','tipo_user', 'habilidades', 'segmento', 'horas_disponiveis']]

df = df[['user_id','tipo_user', 'segmento', 'horas_disponiveis', 'python', 'php', 'js',
       'scrum', 'illustrator', 'laravel', 'html', 'angular', 'css', 'ionic',
       'scss', 'big-data', 'machine-learning', 'scikit-learn', 'photoshop']]


# In[ ]:

# --------------------------- EXTRA ----------------------------- #
# Código para pré-processamento do df
import sklearn.preprocessing as preprocessing
# Preprocessing data
# Labeling Segmento Column
label_encoder = preprocessing.LabelEncoder()
label_encoder.fit(df_categ['segmento'])
label_encoder.classes_
df_categ['segmento'] = label_encoder.transform(df_categ['segmento'])

# Labeling tipo_user Column
label_encoder.fit(df_categ['tipo_user'])
label_encoder.classes_
df_categ['tipo_user'] = label_encoder.transform(df_categ['tipo_user'])

# creating linear vector with the habilidades classes
classes = []
for i in range(len(df_categ['habilidades'])):
    classes_line = df_categ['habilidades'][i].split(',')
    
    for j in range(len(classes_line)):
        
        classes.append(classes_line[j].strip())

# Creating columns with classes names and starting it's value with 0
for i in range(len(classes)):
    df_categ[classes[i]] = 0
# Modifying columns to '1' when habilidade is found
   
for i in range(len(df['habilidades'])):
    classes_line = df_categ['habilidades'][i].split(',')
    
#     print(classes_line)
    for j in range(len(classes_line)):
        classe = classes_line[j].strip()
        if classe in classes:
            df_categ.loc[:, (classe)][i] = 1
#             print(classes_line[j])
#     print("--------")

del df_categ['habilidades']
df_categ.to_csv(path_or_buf='./data_processed.csv', sep=';')


# In[17]:

#2) Separar conjunto de treino e de teste

limit = int((len(df)*0.7)) # queremos 70% para treino
X_treino = df[:limit]
X_teste = df[limit:].reset_index(drop=True)
X_treino.columns


# In[18]:

#3) Implementar algoritmo de rankeamento para cálculo de probabilidade

# Implementacao para mais de uma linha de teste
from IPython.core.debugger import Tracer
matches_row  = {}
# matches_prob = {}
'''
    Função que gera um dicionario de rankings dado um conjunto de teste(à ser recomendado) 
    e um conjunto de treinamento para realizar a recomendação
'''
# Do jeito que rank_the_data está hoje, estamos sujeitos à ter que fazer manutenção constante no código
# Somente na parte dos pesos, talvez tornamos ele um dicionario cuja chave seja o nome da coluna com seu valor
# o peso respectivo => TODO <=
def rank_the_data(X_treino,X_teste, name_treino='Ranking_Treino', name_teste='Ranking_Teste'):
    
    temp_matches = {}
    matches_dict = {}
    
    for row in X_teste.itertuples(name=name_teste): # definindo a row atual do x_teste
        match = False
        valores_teste = []
        valores_treino = []
        rating = 0
        pesos = (len(row) - 3) * [0.0] #array com os pesos
        pesos[0] = 0.8 # aumentando peso do segmento para quando houver match
        
        for i in range(2,len(pesos)):
            pesos[i] = 1.0 # aumentando o peso das habilidades
        # para a disponibilidade de horas nós temos que fazer um calculo mais detalhado
        # diponibilidade_startup > disponibilidade_user; disponibilidade_user/disponibilidade_startup => peso
        # diponibilidade_startup < disponibilidade_user; disponibilidade_startup/disponibilidade_user => peso
        
        
        for i in range(3,len(row)):  
        # aqui é o loop do item da linha (colunas) começamos do index 2 por causa da estrutura da tupla
            valores_teste.append(row[i])

        for row_treino in X_treino.itertuples(name=name_treino):# loop da row atual do x_treino
            for i_treino in range(3, len(row_treino)): # loop dos itens da linha (colunas)
                valores_treino.append(row_treino[i_treino]) # valor da coluna

            if not(row.tipo_user == row_treino.tipo_user): # nao podemos computar valores para usuarios de mesmo tipo
                # para adicionar funcionalidade de peso teremos que modificar a partir da current_sum
                # pensamento: e se já de inicio nós tivermos um array com todos os pesos settados com 1 e fizermos
                # a multiplicação
                
                #peso disp_horas
                if row.horas_disponiveis > row_treino.horas_disponiveis:
                    pesos[1] = row_treino.horas_disponiveis/row.horas_disponiveis
                elif row.horas_disponiveis == row_treino.horas_disponiveis:
                    pesos[1] = 0.9 # se o horário for igual devemos aumentar o peso padrão
                else:
                    pesos[1] = row.horas_disponiveis/row_treino.horas_disponiveis
                # calculamos o peso das horas, mas ainda precisamos lidar com o problema maior
                # como fazer a multiplicacao do peso pelo item na posicao
                #EUREKA: Só precisamos da soma do peso[5]
                Tracer()()
                current_sum = (sum(np.equal(valores_teste, valores_treino)*pesos)+ pesos[1])/(len(X_teste.columns) - 2)
                rating = np.around(current_sum, decimals=2)
                temp_matches[rating] = row_treino
            valores_treino = [] #resetamos o valor a cada iteração que a row de treinamento muda
            
        matches_dict[row] = temp_matches
        temp_matches = {}
        
    return matches_dict

#chamando funcao de rankeamento
matches_row = rank_the_data(X_treino, X_teste)


# In[13]:

# Nós ordenamos o matches_row pro dado ficar mais organizado (passo opcional) 
matches_row = collections.OrderedDict(sorted(matches_row.items(), reverse=True))
# print(matches_row)


# In[14]:

#4) Filtrar saídas do algoritmo de rankeamento

def filter_ranked_data (matches_dict, min_val=0.65):
    results = {}
    for key,value in matches_dict.items():
        filter = {k:v for k,v in value.items() if k >= min_val}
        for k,v in filter.items():
            results[key.user_id] = {k:v.user_id for k,v in filter.items()}
    return results
   


# In[15]:

filtered_results = filter_ranked_data(matches_row, min_val=0.75) # dicionario com chave = user_id do teste e valores = dic(nota:user_id do treino)
# print(filtered_results)


# In[16]:

#5) Mostrar para o usuário os resultados filtrados com as taxas de recomendação

#Agora temos que pegar o results e formatar de uma forma que se torne uma recomendação de verdade:
def visualize_recommendations(filtered_dict, categoric_df):
    
    for key, value in filtered_dict.items():
        test_data = categoric_df.loc[key]
        columns = categoric_df.columns
        print("-----------------------")
        print("Dado para teste: ")
        print("-----------------------")
        for i in range(len(test_data)):
            print("{0}: {1}".format(columns[i], test_data[i]))
        print("---------------------------------------------")
        print("Recomendações: ")
        print("-----------------------")
        value = collections.OrderedDict(sorted(value.items(), reverse=True)) #ordenando notas
        for k,v in value.items():
            rating = k
            rating_user = categoric_df.loc[v]
            print("Recomendação: %.2f%%" % (rating*100))
            for i in range(len(rating_user)):
                print("{0}: {1}".format(columns[i], rating_user[i]))
            print("----")
visualize_recommendations(filtered_results, df_categ)


# #### Teste do algoritmo
# ### Nós criamos um conjunto para treino e um para teste e aplicamos as funções
# Nós pegamos os campos-chave da aplicação e transformamos em um dataFrame

# ### Dataframes

# #### Df com os dados categóricos
# Esse é nosso dataframe com os dados categóricos, é um dataframe criado de acordo com os dados crus que receberíamos da aplicação

# In[14]:

df_categ.head()


# #### Df sem dados categóricos
# Esse é nosso dataframe com os dados não categóricos, nós fizemos um pré-processamento e tornamos todas as classes que tinham algum nome algum valor numérico que as represente

# In[12]:

df.head()


# In[10]:

# Testes do algoritmo
X_treino = df[:(len(df) - 1)]
X_teste = df[(len(df) - 1):].reset_index(drop=True)
print("Quantidade de dados para treino: %d" % len(X_treino))
print("Quantidade de dados para teste: %d" % len(X_teste)) # queremos apenas um dado para teste
print("Quantidade total de dados: %d" % len(df))


# In[11]:

ranked_data = rank_the_data(X_treino,X_teste)
filtered_data = filter_ranked_data(ranked_data)
visualize_recommendations(filtered_data, df_categ)


# In[155]:

# TODO:
#    - Conseguir pegar dados das notas(pegar os campos iguais, para mostrar o porque do 'match') - OK
#    - Criar funções para realizar o rankeamento - OK
#    - Separar notas por linha de x_teste - OK
#    - Trabalhar implementação de apenas uma entrada de teste - OK

#TODO:
    - Implementar pesos para os campos - OK
    - Implementar peso para horas disponiveis - OK
        - Podemos pegar a % entre o tempo pedido pela startup e o que o user disse estar disponivel
        - Após % devemos * por 1 para ter o qtd de pontos sem ser 0
        - Ex(Startup: 6 horas; user: 4 horas => 4/6 = 66%; 66%*1,0 = 0,66 ==> Esse valor seria adicionado ao calculo)