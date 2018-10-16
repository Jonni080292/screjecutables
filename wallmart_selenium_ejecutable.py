import requests
import re
import pandas as pd
from bs4 import BeautifulSoup


import logging
import time



LOG_FILENAME = 'logging_Wallmart.out'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    )
logging.debug('Wallmart')
logging.debug('*************************************')
logging.debug('Inicio : ' + (time.strftime("%H:%M:%S")))


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



sql_ligas = 'select * from farmacia_ligas where id_farmacia = 3'
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





url='https://super.walmart.com.mx/Farmacia/Medicamentos-de-Patente/A/_/N-7tm?No=0&Nrpp=32'


from selenium import webdriver

browser = webdriver.Firefox() #replace with .Firefox(), or with the browser of your choice



for row in result:
        #print('row = %r' % (row[2],))
        url=row[2]
        categoria = row[1]
        for numero_pagina in range(0,row[3]):
                numero= numero_pagina*20 
                #print(url[:-2])
                url_categoria = url[:-2] + format(numero) 
                #print(url_categoria)

                try:
                 browser.get(url_categoria)

                 soup = browser.page_source
                 soup = BeautifulSoup(soup, 'html.parser')
                except:
                    logging.debug('problema conexion',url_categoria)
                    pass 
                lista_nombre_productos = soup.find_all('p')
                lista_url_productos = soup.find_all('img',alt=True)
                list_url_imagen= soup.find_all('a',href=True)

                #browser.close()
                bandera = 0
                item=0
                L_imagen=[]
                L_producto=[]
                L_precio=[]
                L_sku=[]
                p=0
                prod_ant='XXX'
                for imagen in list_url_imagen:
                         imagen = imagen.get('href')
                         aux_imagen=imagen.split('/')
                         aux = aux_imagen[-1]
                         if len(aux_imagen[-1])==14 and aux[:1]=='0':   
                                if item==0:
                                   L_imagen.append(imagen)
                                else:
                                   if L_imagen[-1]!=imagen:
                                      L_imagen.append(imagen)
                                item = item +1
                                
                contador=0
                for producto in lista_nombre_productos:
                       if producto.text[:3]==('max'):
                                bandera = 1
                       if producto.text==('Contáctanos'):
                                bandera = 0
                       if bandera == 1  and producto.text[:3] !=('max'):
                              texto=producto.text
                              if prod_ant[:1]=='$' and texto[:1]=='$':
                                 L_precio[-1]=texto
                              #print(producto.text)
                                 prod_ant = texto
                              if texto[:1]!='$' and len(texto)>0:
                                     if (texto[:2])!= '2x' and (texto[:2])!= '3x' and (texto[:2])!= '4x'  :
                                        L_producto.append(texto)
                                        prod_ant = texto
                              if prod_ant[:1]!='$' and texto[:1]=='$' :
                                     L_precio.append(texto)
                                     prod_ant = texto
                               
                              
                                
                        
                for b in lista_url_productos:
                         sku = b.get('src')
                         sku = sku.split('/')
                         sku=sku[-1]
                         if sku[-3:]=='jpg':
                            sku=sku[:14]
                            #print(sku)
                            L_sku.append(sku)
                         
                #print(L_imagen)
                #print(L_producto)
                #print(L_precio)
                #print(L_sku)
                item=0
                for producto_name in L_producto:
                            try:

                                    producto_nombre_aux = producto_name
                                    url_imagen = L_imagen[item]
                                    sku=L_sku[item]
                                    presentacion='NA'
                                    presentacion_aux2='NA'
                                    sustancia = 'NA'
                                    text = L_precio[item]
                                    text = text.replace("M.N.","")
                                    text= text.replace(",","")
                                    text= text.replace("$","")
                                    precio = text
                                   
                                   
                                    item = item +1
                                    producto_nombre_nuevo = producto_nombre_aux.replace("'"," ")
                                    producto_nombre_nuevo= producto_nombre_nuevo.replace("."," ")
                                    producto_nombre_nuevo= producto_nombre_nuevo.replace("(","")                             
                                    

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
         
                                   
                                       if  re.search(r"[0-9]/[0-9]",a) :
                                       
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
                                                #print(a)
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


                      
                                    text = ""
                                    try:
                                     id_item=id_item+1   
                                     sql = ("insert into Productos values (3," + format(id_item) + ",'" + sku 
                                         + "','" + nombre.strip()
                                         + "','" + producto_nombre_nuevo.strip()
                                         + "','" + lab + "','"
                                         +  sustancia + "','" + presentacion_aux2.strip()
                                         + "','" + contenido.strip()
                                         + "','" + unidades
                                         + "','" + tipo.strip()
                                         + "','" + unidades2 
                                         + "'," + format(precio) + "," + format(categoria)
                                         + ",GETDATE() ,'https://super.walmart.com.mx" + url_imagen + "')")
                                     #print(sql)
                                      
                                     cursor.execute(sql)
                                     cursor.commit()
                                    except:
                                     logging.fatal('error al grabar el registro datos:' + sql)
                                     pass
                                    lin=0
                                    producto = ""
                                    lab=""
                                    presentacion=""
                                    sustancia=""
                                    precio = 0
                                    plin=0

                            except:
                              
                              logging.debug('Error registros ya existentes')
                              pass
browser.close()


try:
    sql = ("exec SP_Actualiza_catalogo 3")
    cursor.execute(sql)
    cursor.commit()
except:
  logging.debug('error al actualizar el catalogo datos:',)
pass



logging.debug('fin La comer: ' + (time.strftime("%H:%M:%S")))        

