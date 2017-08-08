import pandas as pd

import numpy as np
import collections
import sklearn.preprocessing as preprocessing

class Ranking (object):

    def __init__(self,df,preprocessed=True):
        self.df = df

    def getDf (self):
        return self.df

    def preprocessDataFrame (self):# testar se é preciso receber df como parametro
        categorical_columns = self.df.select_dtypes(['object']).columns
        label_encoder = preprocessing.LabelEncoder()
        for column in categorical_columns:
            label_encoder.fit(self.df[column])
            label_encoder.classes_
            self.df[column] = label_encoder.transform(self.df[column])
        return self.df

    def train_test_split (self,test_size=0.6):
        limit = int((len(self.df)*test_size))
        X_treino = self.df[:limit]
        X_teste = self.df[limit:].reset_index(drop=True)
        return X_treino, X_teste


    '''
        Função que gera um dicionario de rankings dado um conjunto de teste(à ser recomendado)
        e um conjunto de treinamento para realizar a recomendação
    '''
    # Do jeito que rank_the_data está hoje, estamos sujeitos à ter que fazer manutenção constante no código
    # Somente na parte dos pesos, talvez tornamos ele um dicionario cuja chave seja o nome da coluna com seu valor
    # o peso respectivo => TODO <=
    def rank_the_data(self,X_treino,X_teste, name_treino='Ranking_Treino', name_teste='Ranking_Teste'):

        temp_matches = {}
        matches_dict = {}

        for row in X_teste.itertuples(name=name_teste): # definindo a row atual do x_teste
            match = False
            valores_teste  = []
            valores_treino = []
            rating = 0
            pesos  = (len(row) - 3) * [0.0] #array com os pesos

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

                    current_sum = (sum(np.equal(valores_teste, valores_treino)*pesos)+ pesos[1])/(len(X_teste.columns) - 2)
                    rating = np.around(current_sum, decimals=2)
                    temp_matches[row_treino] = float(format(rating, '.2f'))
                valores_treino = [] #resetamos o valor a cada iteração que a row de treinamento muda

            matches_dict[row] = temp_matches
            temp_matches = {}

        return matches_dict

    def filter_ranked_data (self,matches_dict, min_val=0.65):
        results = {}
        for key,value in matches_dict.items():
            filtered = {k:v for k,v in value.items() if v >= min_val}

            for k,v in filtered.items():
                results[key.user_id] = {k.user_id:v for k,v in filtered.items()}

        return results #retornamos um dicionario com os dados filtrados, isso é o que temos que mandar através da api e tratar

    def visualize_recommendations(self,filtered_dict, categoric_df):

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

            value = collections.OrderedDict(sorted(value.items(),key=lambda x: x[1],reverse=True)) #ordenando por valores(ratings)

            for k,v in value.items():
                rating = v
                rating_user = categoric_df.loc[k]
                print("Recomendação: %.2f%%" % (rating*100))
                for i in range(len(rating_user)):
                    print("{0}: {1}".format(columns[i], rating_user[i]))
                print("----")
