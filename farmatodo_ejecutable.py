import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
import logging
import time



LOG_FILENAME = 'logging_Farmatodo.out'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    )
logging.debug('Farmatodo ')
logging.debug('*************************************')
logging.debug('Inicio : ' + time.strftime("%d/%m/%Y") + '   ' + (time.strftime("%H:%M:%S")))

f = open(LOG_FILENAME, 'rt')
try:
    body = f.read()
finally:
   f.close()

    
#**************
# cadena conexion sql server
import pyodbc
server='tcp:orbisprices.database.windows.net'
database='OrbisPrice';
username='PriceExternalLogin@orbisprices'
password='Pr!c3Ext3rn4l082018'

cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)



cursor = cnxn.cursor()
id_item=0

sql_ligas = 'select * from farmacia_ligas where id_farmacia=4'
tokens = 'select * from tokens '
cursor.execute(sql_ligas)
result = cursor.fetchall()
tokens = 'select rtrim(ltrim(token)) token,rtrim(ltrim(token_asignado)) token_asignado, tipo from tokens'
cursor.execute(tokens)
tokens = cursor.fetchall()

d=[]
for row in tokens:
    d.append({'token':row[0],'asignado':row[1],'tipo':row[2]})          

df = pd.DataFrame(d)

lab='NA'
sustancia='NA'

for row in result:
        print('row = %r' % (row[2],))
        url=row[2]
        categoria = row[1]
        cadena = len(url)-7
       
        for numero_pagina in range(row[3]):
          
                    url1 = url[:cadena] 
                    url2 = url[-6:]
                    
                    url_categoria = str(url1) +str(numero_pagina+1) + str(url2)
                    #print(url_categoria)
                    #page = requests.get('"https://www.farmatodo.com.mx/farmacia/?p=3&o=&q="')
                    try:                       
                      page = requests.get(url_categoria)
                      soup = BeautifulSoup(page.text, 'html.parser')
                    except:
                       logging.debug('problema conexion' + url_categoria)
                       pass
                    
                    #print (soup)
                
                 
                    lista_nombre_productos = soup.find_all(class_='col-md-6')
                    lista_precio_productos= soup.find_all(class_='col-md-4')
                   
                    item=0
                    lin=0
                    producto_nombre_aux = ""
                    lab=""
                    presentacion=""
                    sustancia=""
                    precio=0
                    
                    for Pprecio in lista_precio_productos:
               
                        prod = lista_nombre_productos[item].text

                        for b in lista_nombre_productos[item].find_all('a', href=True):
                            url_imagen = b.get('href')

                        
                        sku=0
                        for a in Pprecio.find_all('input', id=True):
                                    s = a['id'].split(' ')
                                    k=len(s[0])-8
                                    
                                    sku=s[0][-k:]
                                    #print (sku)
                                                        
                        lines = (line.strip() for line in prod.splitlines())
                        # break multi-headlines into a line each
                        chunks = lines #(phrase.strip() for line in lines for phrase in line.split("  "))
                        # drop blank lines
                        text = '\n'.join(chunk for chunk in chunks if chunk)
                      
                        for line in text.splitlines():
                                
                                if lin == 0 and line != 'BUSCAR' and line[:9] != 'ACEPTAMOS':
                                   producto_nombre_aux = line
                                if lin == 1 :
                                  lab = line[12:]
                                if lin == 2 :
                                  presentacion = line[13:]
                                if lin == 3 :
                                  sustancia = line[7:]
                                if lin == 3 and line == 'Indicaciones Terapéuticas':
                                  sustancia = 'NP'
                                lin = lin +1
                       
                        #print(producto_name.text)
                        Dprecio = Pprecio.text
                        lines = (line.strip() for line in Dprecio.splitlines())
                        # break multi-headlines into a line each
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        # drop blank lines
                        text = '\n'.join(chunk for chunk in chunks if chunk)
                       
                        for pp in text.splitlines():
                              pp=pp.replace(",","")  
                              if pp[:1] == '$':
                               precio = pp

                        if item <=  len(lista_nombre_productos)-5:

                                
                                 producto_nombre_nuevo = producto_nombre_aux.replace("'"," ")
                                 producto_nombre_nuevo= producto_nombre_nuevo.replace("."," ")
                                 producto_nombre_nuevo= producto_nombre_nuevo.replace("(","")
                                #print(producto_nombre_nuevo)
                                #print(lab)
                                                         
                                 presentacion_aux2=presentacion.replace(","," ")
                                #print(presentacion_aux2)
                                #print(sustancia)
                                
                                 precio_nuevo = precio
                                #print(precio_nuevo)
                                
                        
                        item = item +1
                        id_item = id_item +1


                        #text mining bag of words
                        words = producto_nombre_nuevo.split()
                        nombre=producto_nombre_nuevo
                        contenido=" "
                        unidades=""
                        unidades2=""
                        tipo=""
                        num_unidades=0
                        

                        num_word=0
                                

                        for word in words:
                 
                           a=word.upper()
                           try:
                              b=(df.loc[df['token']==a])
                              if ( b.iloc[0]['tipo']) == 1:
                                 ban=1
                                 contenido = b.iloc[0]['asignado']
                                 nombre = nombre.replace(word,"")
                                 sustancia=sustancia.replace(word,"")
                                 if  (words[num_word -1].isdigit()):
                                      unidades = words[num_word -1]
                                      nombre = nombre.replace(words[num_word -1],"")
                                      sustancia=sustancia.replace(words[num_word -1],"")
                                 else:
                                  if  (words[num_word + 1].isdigit()):
                                      unidades = words[num_word +1]
                                      nombre = nombre.replace(words[num_word +1],"")
                                      sustancia=sustancia.replace(words[num_word +1],"")

                                     
                              else:
                                if tipo=="":
                                  ban=2
                                  tipo=  b.iloc[0]['asignado']
                                  nombre = nombre.replace(word,"")
                                  sustancia=sustancia.replace(word,"")
                                  if  (words[num_word -1].isdigit()):
                                      unidades2 = words[num_word -1]
                                      nombre = nombre.replace(words[num_word -1],"")
                                      sustancia=sustancia.replace(words[num_word -1],"")
                                    
                                  
                           except:
                             pass

                       
                           if  re.search(r"[0-9][0-9]*/[0-9][0-9]*",a) :
                           
                                if num_unidades == 0 and ban==2: 
                                        unidades2=word
                                        num_unidades=1
                                else:
                                        unidades=word
                                nombre = nombre.replace(word,"")
                                sustancia=sustancia.replace(word,"")
                                unidades2 = word[-1]
                           else:
                                
                                if re.search(r"[0-9][0-9]M*",a) or re.search(r"[0-9][0-9]G*",a) :
                                    a = word[-2:]
                                    a = a.upper()
                                    print(a)
                                    try:
                                        b=(df.loc[df['token']==a])
                                        if ( b.iloc[0]['tipo']) == 1:
                                             contenido = b.iloc[0]['asignado']
                                             nombre = nombre.replace(word,"")
                                             sustancia=sustancia.replace(word,"")
                                        else: 
                                              tipo=  b.iloc[0]['asignado']
                                              unidades2 = word[:-2]
                                              num_unidades=1
                                              nombre = nombre.replace(word,"")
                                              sustancia=sustancia.replace(word,"")
                                    except:
                                        pass
                                    
                                    nombre = nombre.replace(word,"")
                           num_word = num_word +1 


                  
                        if len(sustancia)> 150:
                                sustancia = sustancia[:140]
                        if sku != 0:
                                try:
                                        sql = ("insert into Productos values (4," + format(id_item) + ",'" + sku 
                                         + "','" + nombre.strip()
                                         + "','" + producto_nombre_nuevo.strip()
                                         + "','" + lab + "','"
                                         +  sustancia + "','" + presentacion_aux2.strip()
                                         + "','" + contenido.strip()
                                         + "','" + unidades
                                         + "','" + tipo.strip()
                                         + "','" + unidades2 
                                         + "'," + format(precio) + "," + format(categoria)
                                         + ",GETDATE() ,'https://www.farmatodo.com.mx" + url_imagen + "')" )
                                        #print(sql)

                                        cursor.execute(sql)
                                        cursor.commit()
                                except:
                                  logging.debug('error al grabar el registro datos:' + sql)
                                  pass
                                

                        lin=0
                        producto = ""
                        lab="NA"
                        presentacion=""
                        sustancia="NA"



try:
    sql = ("exec SP_Actualiza_catalogo 4")
    cursor.execute(sql)
    cursor.commit()
except:
  logging.debug('error al actualizar el catalogo datos:',)
pass

logging.debug('Termino Farmatodo : ' + (time.strftime("%H:%M:%S")))






