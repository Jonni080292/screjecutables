import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
import logging
import time



LOG_FILENAME = 'logging_FarmaciaDelAhorro.out'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    )
logging.debug('Farmacia del Ahorro ')
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



sql_ligas = 'select * from farmacia_ligas where id_farmacia=2'
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
       
        for numero_pagina in range(row[3]):
         try:
            url_categoria = url + format(numero_pagina+1)
            
            print(url_categoria)
            #page = requests.get('https://www.farmaciasanpablo.com.mx/medicamentos/c/06')
            page = None
            while page is None:
                    try:
                        
                         page = requests.get(url_categoria)
                    except:
                         logging.debug('problema conexion',url_categoria)
                         pass


            soup = BeautifulSoup(page.text, 'html.parser')
            #print (soup)
        
            lista_sku_productos =soup.find_all(class_='product-image')
            lista_nombre_productos = soup.find_all(class_='product-name')
            lista_nombre_presentacion = soup.find_all(class_= 'product-name')
            lista_precio_productos= soup.find_all(class_='price')
         
            item=0
            for producto_name in lista_nombre_productos:

                im =  lista_sku_productos[item].find_all('img')
                imagen = im[0].get('src')
                sku = imagen.split('/')
                sku = sku[-1]
                sku=sku[:-6]

                for a in producto_name.findAll('a',href=True):
                          url_imagen = a.get('href')


                for letter in 'abcdefghijklmnñopqrstuvwxyz-_':
                    sku = sku.replace(letter, '')
               
                #print(sku[:-6])
                #print(producto_name.text)
                #print(lista_nombre_presentacion[item].text)
                #print(lista_precio_productos[item].text)
                producto_nombre_aux = producto_name.text
                producto_nombre_nuevo = producto_nombre_aux.replace("'"," ")
                producto_nombre_nuevo= producto_nombre_nuevo.replace("."," ")
                producto_nombre_nuevo= producto_nombre_nuevo.replace("(","")

                presentacion_aux = lista_nombre_presentacion[item].text
                presentacion_aux1=presentacion_aux.replace("'"," ")
                presentacion_aux2=presentacion_aux1.replace(","," ")
                
                precio= lista_precio_productos[item].text
                precio = precio.replace(",","") 
                precio = precio.replace("MXN","")
                precio = precio.replace("$","") 


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
         
                
                sql = ("insert into Productos values (2," + format(id_item) + ",'" + sku 
                         + "','" + nombre.strip()
                         + "','" + producto_nombre_nuevo.strip()
                         + "','" + lab + "','"
                         +  sustancia + "','" + presentacion_aux2.strip()
                         + "','" + contenido.strip()
                         + "','" + unidades
                         + "','" + tipo.strip()
                         + "','" + unidades2 
                         + "'," + format(precio) + "," + format(categoria)
                         + ",GETDATE() ,'" + url_imagen + "')")
                #print(sql)
                cursor.execute(sql)
                cursor.commit()
         except:
           logging.debug('error al grabar el registro datos:' + sql)
           pass


try:
    sql = ("exec SP_Actualiza_catalogo 2")
    cursor.execute(sql)
    cursor.commit()
except:
  logging.debug('error al actualizar el catalogo datos:',)
pass



logging.debug('fin Farmacia del ahorro : ' + (time.strftime("%H:%M:%S")))
