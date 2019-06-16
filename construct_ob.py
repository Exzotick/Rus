import pandas as pd
import numpy as np
n_levels = 10


#Даункастинг типов для экономии памяти
df = pd.read_csv('/content/drive/My Drive/EURRUB.txt')
df = df.drop(['NO', 'SECCODE', 'TRADENO', 'TRADEPRICE'], axis=1)
df['ORDERNO'] = pd.to_numeric(df['ORDERNO'], downcast='unsigned')
df['VOLUME'] = df['VOLUME']/1000
df['VOLUME'] = pd.to_numeric(df['VOLUME'], downcast='unsigned')

df['PRICE'] = df['PRICE'].round(4)
df['ACTION'] = pd.to_numeric(df['ACTION'], downcast='unsigned')
df['BUYSELL'] = df['BUYSELL'].map({'B': 1, 'S': -1})
df['BUYSELL'] = pd.to_numeric(df['BUYSELL'], downcast='integer')

#Соединение даты и времени в один столбец формата datetime
df['DATE'] = df['DATE'].astype(str).str[-2:]
df['TIME'] = df['TIME'].astype(str)
df['time'] = pd.to_datetime({'year': '2014',
	                        'month': '09',
	                        'day': df['DATE'],
	                        'hour': df['TIME'].str[:2], 
	                        'minute': df['TIME'].str[2:4], 
	                        'second': df['TIME'].str[4:6], 
	                        'ms': df['TIME'].str[6:]})
df = df.drop(['DATE', 'TIME'], axis=1)
tick = 0.0005

#Удаление записей о рыночных заявках и создание numpy массива из датафрейма
df = df[df['PRICE'] != 0].reset_index(drop=True)
dfmat = df.to_numpy()

#Создание массива для хранения книги заявок
n = df.shape[0]
ob = np.full((n, n_levels*4), np.nan)
ob[:, 1::2] = 0

#Заполнение книги заявок
buy = {}
sell = {}
for i in range(n):
    side = dfmat[i, 0]
    ordno = dfmat[i, 1]
    action = dfmat[i, 2]
    price = dfmat[i, 3]
    volume = dfmat[i, 4]  
    
    
    if action == 1:
        if side == 1:
            buy[ordno] = [volume, price]
        else:
            sell[ordno] = [volume, price]
    elif action == 0:
        if side == 1:
            del buy[ordno]
        else:            
            del sell[ordno]   
    else:
        #print(i)
        if side == 1:
            if volume < buy[ordno][0]:
                buy[ordno][0] -= volume 
            else: 
                del buy[ordno]
        else:
            if volume < sell[ordno][0]:
                sell[ordno][0] -= volume
            else: 
                del sell[ordno]
    
    buy_prices = np.unique(np.array([list(buy.values())[i][1] for i in range(len(buy))]))   
    buy_prices_sorted = sorted(list(buy_prices), reverse=True)
    buy_depth = dict.fromkeys(buy_prices_sorted, 0)
    for b_ord in buy:
        buy_depth[buy[b_ord][1]] += buy[b_ord][0] 
        
    sell_prices = np.unique(np.array([list(sell.values())[i][1] for i in range(len(sell))]))      
    sell_prices_sorted = sorted(list(sell_prices))        
    sell_depth = dict.fromkeys(sell_prices_sorted, 0)
    for s_ord in sell:
        sell_depth[sell[s_ord][1]] += sell[s_ord][0] 
        
    for level in range(min(len(buy_depth), n_levels)):
        ob[i, 4*level] = buy_prices_sorted[level]
        ob[i, 1+4*level] = buy_depth[buy_prices_sorted[level]]
    for level in range(min(len(sell_depth), n_levels)):
        ob[i, 2+4*level] = sell_prices_sorted[level]
        ob[i, 3+4*level] = sell_depth[sell_prices_sorted[level]]

#Создание списка названий столбцов книги заявок
ob_cols = []
for level in range(n_levels):
    ob_cols.append('bid{}p'.format(level+1))
    ob_cols.append('bid{}v'.format(level+1))
    ob_cols.append('ask{}p'.format(level+1))
    ob_cols.append('ask{}v'.format(level+1))

#Создание датафрейма книги заявок из массива
book = pd.DataFrame(data=ob, columns=ob_cols)
time = time.loc[before].reset_index(drop=True)
book['time'] = time

#Удаление из книги записей после 23:50 (время клиринга)
book[book['time'].dt.time >= pd.to_datetime('23:50').time()].index

#Сохранение книги заявок в файл
book.to_csv('clean_book.csv', index=False)