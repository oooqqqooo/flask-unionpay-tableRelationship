# -*- coding: utf-8 -*- 
import sys
import pandas as pd
import re
import shlex
import pickle
import networkx as nx 
import os
import json

name = '\$APP_HOME/|\$HOME/hbkshell/|/DWTNDAPS/usr/dw_hbkas/hbkshell/';shell_dir = 'dw_hbkas/hbkshell/'
wormhole_dir = 'dw_hbkas/wormhole/wormhole-application'
def read_path():
	#  读取生产调度中正在使用的调度ID‘99991231’且‘H’
	data = pd.DataFrame(columns=['jobID','a','b','c','d','END','e','f','CON','g'])
	with open('job_info/tbl_sch_schedule_info.del') as f:
		index = 0
		for i in f.readlines():
			index += 1
			if index==1:
				continue
			#因为有一列括号中也有逗号，所以正常的strip().split()会出错，所以这里用shlex模块处理文件的每一行,posix=True会忽略括号和引号中的逗号
			ss=shlex.shlex(i,posix=True)
			ss.whitespace=' '
			ss.whitesapce_split=True
			ss = list(ss)
			for j in ss:
				if j in [',','\n']:
					ss.remove(j)
			data.loc[index] = ss

	data = data[(data['END']=='99991231') &(data['c']=='H')]
	sche_job = list(data.jobID.astype(int))

	#根据上面获得的所有H 99991231的jobID，在tbl_sch_function_info.del文件中查找job对应建表文件的目录和文件名
	path = [0]*len(sche_job)
	with open('job_info/tbl_sch_function_info.del') as f:
		index=0
		for i in f.readlines():
			index += 1
			if index==1:
				continue
			line = [ j.strip(' ').strip('"') for j in i.strip().split(',')[:4]]
			if int(line[0]) in  sche_job:
				#将路径中类似$APP_HOME的给过滤掉
				#path[sche_job.index(int(line[0]))] = line[3].replace('$APP_HOME/','').replace('hbkshell/','').replace('$HOME/','')
				#.replace('$WORMHOLE_APP_HOME','shell/wormhole').strip('/')+'/'+str(line[2])
				path[sche_job.index(int(line[0]))] =re.sub(name,shell_dir,line[3]).replace('$WORMHOLE_APP_HOME',wormhole_dir).strip('/')+'/'+str(line[2])

	path_df = pd.DataFrame(path,columns=['path'])
	path_df = path_df[path_df['path'].astype(str).str.contains('shell|wormhole',regex=True)]
	path_df = path_df[~path_df['path'].astype(str).str.contains('ueshell')]



	#根据上面的获得的路径读取shell目录下的建表文件中，根据bash关键字获得所有调度相关建表文件的路径
	file=[];bash = [];exce = []
	for i in list(path_df.path):
		try:
			flag = 0 
			with open(i.strip()) as f:
				for j in f.readlines():
					if  'echo ' not in j and 'log ' not in j  :
						b = re.findall('bash(.*?)\.sh', re.sub(r"#.*\n", " ", j), re.IGNORECASE)
						if len(b)>0:
							file.append(i)
							bash.append(b[0].strip()+'.sh')
					if 'bash ' not in j and 'echo ' not in j and 'log ' not in j and 'wormhole_cront' not in j:
						a = re.findall('(.*?)\.sh -', re.sub(r"#.*\n", " ", j), re.IGNORECASE)
						if len(a)>0:
							file.append(i)
							bash.append(a[0].strip().strip('./').strip('. ').strip('/')+'.sh')
					# 异常处理的,最后一起加入file_set
					if 'shellscript' in j : 
						flag = 1
					if flag == 1 and '.sh' in j and 'log'not in j  :
						c = re.findall('S(.*?)\.sh', re.sub(r"#.*\n", " ", j))
						if len(c)>0:
							exce.append(re.findall('(.*)/',i)[0]+'/'+('S'+c[0]+'.sh'))
		except Exception as e:
			print u'入口脚本中路径错误',e

	#bash中变量名的替换
	for index,i in enumerate(bash):
		bash[index] = re.sub(name,shell_dir,i).replace('${WORMHOME_APP_HOME}',wormhole_dir).replace('$WORMHOLE_APP_HOME',wormhole_dir).replace('${SQOOP_HOME}',shell_dir+'shell/sqoop')
		if '$' in bash[index]:
			# 有些用户自定义的变量，如work_dir等都是当前目录，所以直接从file中获取路径名替换变量名
			bash[index] = re.sub(r'(.*?)/',re.findall('(.*)/',file[index])[0]+'/',bash[index])
		if '/'not in bash[index]:
			bash[index] = re.findall('(.*)/',file[index])[0]+'/'+bash[index]
			
	#因为从入口脚本->file->file2-->file3....对读到的文件需要再一次读bash，应该写成一个递归，但是出现bug，这里使用最原始的方法
	Iter = []
	for i in bash:
		if 'FileTransfer.sh' not in i and '/' in i and 'sqoop'not in i:   # 有部分FileTransfer.sh无效文件直接忽略，sqoop文件也不用读
			try:
				f = open(i.strip(' '),'r')
			except Exception as e:
				print u'递归读取bash时有文件不存在',e
				continue
			for j in f.readlines():
				b = re.findall('bash(.*?)\.sh', re.sub(r"#.*\n", " ", j), re.IGNORECASE)
				if len(b)>0:
					temp = re.sub(name,shell_dir,b[0]+'.sh').replace('$WORMHOLE_APP_HOME',wormhole_dir).replace('${WORMHOLE_APP_HOME}',wormhole_dir).replace('${SQOOP_HOME}',shell_dir + 'shell/sqoop')
					if 'FileTransfer.sh' not in temp and '/' in temp and 'sqoop'not in temp:
						Iter.append(temp)
						try:
							f1 =  open(temp.strip(' '),'r')   # 经过自己查看只会往下读两层，因此再读一次就ok了
						except Exception as e:
							print u'递归读取bash时有文件不存在L2',e
							continue
						for k in f1.readlines():
							bb = re.findall('bash(.*?)\.sh', re.sub(r"#.*\n", " ", k), re.IGNORECASE)
							if len(bb)>0:
								temp = re.sub(name,shell_dir,bb[0]+'.sh').replace('$WORMHOLE_APP_HOME',wormhole_dir).replace('${WORMHOLE_APP_HOME}',wormhole_dir).replace('${SQOOP_HOME}',shell_dir + 'shell/sqoop')
								if 'FileTransfer.sh' not in temp and '/' in temp and 'sqoop'not in temp:
									Iter.append(temp)

	bash_file = bash #备份，然后传递参数给sqoop_read函数
	d = pd.DataFrame()
	d['file'] = file;d['bash'] = bash;d.to_csv('table_file/file_bash.csv',index=0)
	bash.extend(list(path_df['path']))
	bash.extend(Iter)
	bash.extend(exce)
	file_set = list(set([i.strip(' ') for i in bash]))
	return file_set,bash_file,file

def sqoop_read(bash,file):
	###	这里处理sqoop目录下的表依赖关系，因为要用到bash和file变量，所以直接放到了这里
	file_w = open('table_file/sqoop_tbl.txt','w')
	sqoop_file = [];sqoop_export_file = [];rely = [];table = []
	for i,item in enumerate(bash):
		if 'SQOOP.sh' in item:
			with open(file[i]) as f:
				for j in f.readlines():
					if '.sh -' in j.lower() and '#' not in j:
						line = j.strip().split(' ')
						for k in line:
							if '-f' in k:
								# 有一个文件中用户自定义了路径，为了偷懒直接在这里replace了
								ffile = shell_dir+'shell/sqoop/'+ k.replace('-f','').replace('${CPH_JSON}','SOR_UNION_CPH_RELATION.json').replace('${CP_JSON}','SOR_UNION_CP_RELATION.json').replace('${PPH_JSON}','SOR_UNION_PPH_RELATION.json')
								if ffile not in sqoop_file:
									sqoop_file.append(ffile)
									try:
										with open(ffile,'r') as f1:
											tmp = []
											db = json.load(f1)
											db2 = (db['db2_schema']+'.'+db['db2_table']).encode('utf-8')
											hive = db['hive_table']
											tmp.append(db2);rely.append(tmp);table.append(hive)
											file_w.write(ffile + '\t' + hive + '\t'+ str(tmp) + '\n')
									except Exception as e:
										pass
		if 'SQOOP_EXPORT.sh' in item:
			with open(file[i]) as f:
				for j in f.readlines():
					if '.sh -' in j.lower() and '#' not in j:
						line = j.strip().split(' ')
						for k in line:
							if '-cf' in k:
								temp = k.replace('-cf','')
							if '-ph' in k:
								ffile = k.replace('-ph','').replace('$HOME/hbkshell/',shell_dir).replace('$APP_HOME/',shell_dir)+ '/' + temp
								if ffile not in sqoop_export_file:
									sqoop_export_file.append(ffile)
									with open(ffile,'r') as f1:
										tmp = []
										db = json.load(f1)
										db2 = (db['db2_schema']+'.'+db['db2_table']).encode('utf-8')
										hive = db['hive_table'].encode('utf-8')
										tmp.append(hive);rely.append(tmp);table.append(db2)
										file_w.write(ffile + '\t' + db2 + '\t'+ str(tmp) + '\n')
	file_w.close()
	return rely,table

def wormhole_read(file_set,rely,table):
	wormhole_file = []
	#  这三个文件也比较特殊，从file_set->wormhole_file后本来应该能读出json文件，但这三个文件需要进行再次读DIR，因此以特例的形式加在这里
	appen = ['dw_hbkas/wormhole/wormhole-application/his/tshis/tbl_tshis_onl_ins_token/S_LD_D_TSONL_INS_TOKEN.sh',
	'dw_hbkas/wormhole/wormhole-application/his/pphis/tbl_pphis_onl_trans_log/S_LD_D_PPONL_TRANS_LOG.sh',
	'dw_hbkas/wormhole/wormhole-application/his/tshis/tbl_tshis_onl_token_inf/S_LD_D_TSONL_TOKEN_INF.sh']
	def wormhole_file_read(file): #先获取所有路径中wormhole下的文件，从中可以读取到wormhole路径下.sh文件，
		for i,item in enumerate(file):
			if 'wormhole' in item or 'WORMHOME' in item:
				try:
					with open(item,'r') as f:
						ss = f.read()
						ss = re.sub(r"#.*\n", " ", ss)  # 去除注释
						Dir = re.findall('DIR="(.*?)"\n', ss, re.IGNORECASE)
						tasks = re.findall('\$DIR(.*?)\n', ss, re.IGNORECASE)
						for j,ta in enumerate(tasks):
							wormhole_file.append(Dir[0].replace('$WORMHOLE_APP_HOME',wormhole_dir) + ta)
						if len(Dir)==0:
							wormhole_file.append(item)

				except Exception as e:
					print u'所有文件路径file_set中wormhole文件有些不存在',e
	wormhole_file_read(file_set)
	wormhole_file_read(appen)
	wormhole_file.extend(list(file_set))
	json_file=[]
	for i in set(wormhole_file):  #再根据.sh文件读取job__.json文件
		#fff = re.findall('(.*)/',i)[0]
		try:
			with open(i,'r') as f:
				for j in f.readlines():            
					if 'wormhole_crontab' in j:
						json_file.append(re.findall('-s(.*)\n',j)[0].replace('${WORMHOLE_APP_HOME}',wormhole_dir))
		except Exception as e:
			print u'wormhole获取的文件路径有些不存在',e
			
	fro = [];ins = []
	for i in set(json_file):#从job__.json文件中可以读到同目录下的R__.json and W__.json文件名，最终可以获得表依赖关系
		try:
			with open(i,'r') as f:
				db = json.load(f)
				reader = db['reader']['props']['reader.configfile.path'].replace('${WORMHOLE_APP_HOME}',wormhole_dir)
				writer = db['tasks'][0]['writers'][0]['props']['writer.configfile.path'].replace('${WORMHOLE_APP_HOME}',wormhole_dir)
				with open(reader,'r') as f1:
					ss = f1.read()
					ss = ss.lower().replace('\n'or','or'$',' ')  #预处理  根据所有的sh文件内容
					ss = re.sub(r"\s{2,}|,|\$", " ", ss)
					fro_word = re.findall('from(.*?)"',ss)[0].split()  #从R___.json文件中中匹配到的from语句
					fro_temp = []
					for j,item in enumerate(fro_word):
						if j == 0:
							if '{' in fro_word[0]:
								print u'wormhole文件中reader文件表名不规范,需手工处理',i
								break
							if '_' in fro_word[0]:
								 fro_temp.append(fro_word[0])
						elif item == 'from' or item == 'join':
							if '_' in fro_word[j+1]:
								 fro_temp.append(fro_word[j+1])
					if len(fro_temp)==0:
						print u'wormhole文件中reader文件表名不规范,需手工处理',i
						continue
					if len(fro_temp)>2:
						fro_temp = [fro_temp[0]]
					fro.append(fro_temp)
					rely.append(fro_temp)
				with open(writer,'r') as f2:
					for k in f2.readlines():
						if 'hiveDB' in k:
							hiveDB =re.findall('"hiveDB":"(.*)",',k)[0]
						if 'hiveTbl' in k :
							hiveTbl = re.findall('"hiveTbl":"(.*)",',k)[0]
					ins.append(hiveDB+'.'+hiveTbl)
					table.append(hiveDB+'.'+hiveTbl)
		except Exception as e:
			print u'wormhole文件的路径出错',i,e
	file_w = open('table_file/wormhole_tbl.txt','w')
	for i in range(len(fro)):
		file_w.write(str(ins[i]) + '\t'+ str(fro[i]) + '\n')
	file_w.close()
	return rely,table


## 读取shell脚本中自定义表名
def shell_defined(path,var):
	dic_s = {}
	with open(path) as f2:
		for k in f2.readlines():
			k = k.upper()
			if var+'=' in k:
				line = k.strip().split('=')
				if "HBK" in line[1]:
					dic_s[line[0]]=line[1].lower().replace('${hbk}','hbkdb')
				else:
					dic_s[line[0]]=line[1].lower()
	return dic_s

dic={} #读取配置文件中自定义的表名
with open('dw_hbkas/hbkshell/shell/conf/table.conf') as f:
	for i in f.readlines():
		if 'HBASE' in i:
			continue
		i = re.sub(r'#.*\n','',i)
		i = i.replace('export ','').replace('${HBK}','hbkdb').strip(' ')
		l = i.strip().split('=')
		if 'HIVE' in l[0]:
			l[1] = 'hbkdb.'+l[1]
		if len(l)>1:
			dic[l[0]]=l[1].strip(' ')
            
def all_path(file_set,rely,table):
	#获取的依赖关系
	file = open('temp/table.txt','w')
	num = 0;man=[];
	#报编码错误，改成‘latin-1’后通过
	for apath in file_set:
		if '/' not in apath or 'fileSendClient' in apath :
			continue
		try:
			f = open(apath.strip())
		except Exception as e:
			#测试的时候shell文件不是最新，有些文件没有
			#print e 
			print u'获得的所有文件路径file_set，有些不存在',e
			continue
		ss = f.read()
		ss = re.sub(r"#.*\n", " ", ss)  # 去除注释
		ss = ss.replace('\n'or'\t',' ')  #预处理  根据所有的sh文件内容
		ss = re.sub(r"\s{2,}", " ", ss)
		#a = re.findall(r'SQL="(.*?)"log', ss, re.IGNORECASE)
		#匹配sql语句 一个sql语句为一个处理单元 此处写了半天(ㄒoㄒ)
		b = re.findall(r'SQL[_a-z0-9]*="(.*?)log "SQL', ss)  
		for i in b:
			a = re.findall(r'SQL[_a-z0-9]*="(.*)', i)  
			if len(a)>0:
				print u'insert读取异常的文件',apath
				continue
			rely_=[]
			word = i.strip().lower().split(' ')
			# 获得insert后面的表名  insert后面跟的表名都是在insert往后数第三个字符
			try:
				if '$' in word[word.index('insert')+3]:
					t1 = word[word.index('insert')+3].strip('"').strip("'").strip('$').strip('{').strip('}').upper()
					if t1 in dic:
						table_ = dic[t1]
					else:
						dic_shell = shell_defined(apath,t1)
						try:
							table_ = dic_shell[t1]
						except KeyError:
							man.append(apath)
							print u'该sh文件中存在自定义表名，需手工处理',apath,t1,dic_shell
				else:
					table_ = word[word.index('insert')+3]

			#获得from的所有索引，如果下一个是表名则获取，$的需要查表，查不到说明是shell脚本中自定义的，抛异常，需手工处理
				for j,item in enumerate(word): 
					if item=='from' or item=='join':
						if '$' in word[j+1]:
							t2 = word[j+1].strip('$').strip('{').strip('}').strip(')').strip(';').upper()
							if t2 in dic:
								rely_.append(dic[t2])
							else:
								dic_shell = shell_defined(apath,t2)
								try:
									rely_.append(dic_shell[t2])
								except KeyError:
									man.append(apath)     #目前的异常以及全部解决，($TOTALSQL)T可以忽略                                 
									print u'该sh文件中存在自定义表名，需手工处理',apath,t2,dic_shell
						elif  '_' in word[j+1]:
							 rely_.append(word[j+1])
				if len(rely_)>0:
					file.write(apath + '\t' + table_ + '\t'+ str(rely_) + '\n')
				table_ = 'hahaha';rely_=[] ##如果出现异常文件直接会写入hahaha
			except Exception as e:
				if str(e) != "'insert' is not in list":
					print 'ATTENTION!!!!!',e               
	file.close()
	
	## 将依赖关系写入table.txt后，现在开始读取
	filte = ['bushuju','tmp','temp','backup','test']
	filename = []
	file_w = open('table_file/table.txt','w')
	with open('temp/table.txt','r') as f:
		for i in f.readlines():
			line = i.strip().split('\t')
			flag = 0
			for j in filte:
				if j in line[0]:
					flag += 1
			if flag>0:
				continue
			#directory不是表 直接忽略 而${hdfs_hive_path}/bsl/$tblnametmpmon/实质也是directory，且只出现一次 直接过滤，下面对line[2]的处理也是这样
			if line[1].lower()=='directory' or line[1].lower()=='${hdfs_hive_path}/bsl/$tblnametmpmon/':
				continue
			filename.append(line[0])
			if '$' in line[1]:
				try:
					# 虽然在生成table.txt时已经完成了查字典的转化，但是存在嵌套，如用户自定义表名 aTbl = ${stmtrs_bsl_uv_buss_plan}
					line[1] = dic[line[1].strip('"').strip('$').strip('{').strip('}').upper()]
				except Exception as e:
					print line[1]
			table.append(line[1])
			line[2] = eval(line[2])
			if '$' in str(line[2]) or 'dim' in str(line[2]):#'rtapam_dim'
				#将line[2]拷贝了一份，然后遍历拷贝的，对原始的进行修改
				for j,item in enumerate(line[2]):
					if '$' in item:
						if '${gl_hisdb}' in line[2][j] or '${hbkdb}'in line[2][j] or '${HBK}' in line[2][j]:
							line[2][j] = line[2][j].replace('${gl_hisdb}','gl_hisdb').replace('${hbkdb}','hbkdb').replace('${HBK}','hbkdb')
						else:
							line[2][j] = dic[line[2][j].strip('"').strip('$').strip('{').strip('}').upper()]
			file_w.write(line[0] + '\t' + line[1] + '\t'+ str(line[2]) + '\n')
			rely.append(line[2])
	file_w.close()
	return rely,table
def db_script_read(rely,table):
	## 读取db_script中view视图的依赖问题
	file_w = open('table_file/dbscript_tbl.txt','w')
	postfix = set(['hql']);dirname='./dw_hbkas/db/db_script';num=0
	for maindir, subdir, file_name_list in os.walk(dirname):
		for filename in file_name_list:
			apath = os.path.join(maindir, filename)
			if apath.split('.')[-1] in postfix: 
				with open(apath) as f:
					ss = f.read()
					ss = re.sub(r"#.*\n", " ", ss)  # 去除注释
					ss = ss.lower().replace('\n'or'\t',' ')  #预处理  根据所有的sh文件内容
					ss = re.sub(r"\s{2,}", " ", ss)
					if 'create view' in ss:
						tt=[]
						x = ss.strip().split(' ')
						if '_' in x[x.index('create')+2]:
							view = x[x.index('create')+2].strip('(')
						else:
							view = x[x.index('create')+5].strip('(')
						for j,item in enumerate(x): 
							if item=='from' or item =='join':
								if '_' in x[j+1]:
									tt.append(x[j+1].strip('(').strip(')').strip(';'))
						table.append(view)
						rely.append(tt)
						file_w.write(apath + '\t' + view + '\t'+ str(tt) + '\n')
	file_w.close()
	return rely,table

def gen_digraph(rely,table): 
	for ind,nn in enumerate(rely):
		rely[ind] = list(map(lambda x:x.lower(),nn))
	table = list(map(lambda x:x.lower(),table))
	t = pd.DataFrame()
	t['table']=table;t['rely']=rely#;print('&*&*',len(rely));t.to_csv('wahaha',index=0)
	t.to_csv('table_file/table_rely.csv',index=0)
	#edges_nodim过滤了所有维表
	edges_nodim = [(j.strip("'").strip('"').replace('hbkdb.',''),t.iloc[i,0].strip("'").strip('"').replace('hbkdb.','')) for i in range(len(t)) for j in eval(str(t.iloc[i,1])) if 'dim' not in str(j)and 'dim' not in t.iloc[i,0]]
	edges = [(j.strip("'").strip('"').replace('hbkdb.',''),t.iloc[i,0].strip("'").strip('"').replace('hbkdb.','')) for i in range(len(t)) for j in eval(str(t.iloc[i,1])) ]

	def edges_nodes(edges):
		new_edges = [];nodes=[]
		#过滤掉自己指向自己的边
		for i in edges:
			if i[0]!=i[1]:
				new_edges.append(i)
		new_edges = list(set(new_edges))
		for i in edges:
			nodes.append(i[0].strip("'"))
			nodes.append(i[1].strip("'"))
		nodes = list(set(nodes))
		return new_edges,nodes

	new_edges,nodes = edges_nodes(edges) #;print(len(nodes),nodes);print(len(new_edges))
	new_edges_nodim,nodes_nodim = edges_nodes(edges_nodim)

	#有向图 
	DG = nx.DiGraph() 
	#一次性添加多节点，输入的格式为列表 
	DG.add_nodes_from(nodes_nodim) 
	#添加边，数据格式为列表 
	DG.add_edges_from(new_edges_nodim) 
	with open('table_networkx_nodim.pkl','wb')as f:
		pickle.dump(DG,f)
		
	DG2 = nx.DiGraph() 
	DG2.add_nodes_from(nodes) 
	DG2.add_edges_from(new_edges)
	with open('table_networkx.pkl','wb')as f:
		pickle.dump(DG2,f)



if __name__ == '__main__':
	# 可以将rely，table设为全局变量

	file_set,bash_file,file = read_path()
	#sqoop
	rely,table = sqoop_read(bash_file,file)
	#wormhole
	rely,table = wormhole_read(file_set,rely,table)	
	#脚本
	rely,table = all_path(file_set,rely,table)
	#db_script
	rely,table = db_script_read(rely,table)

	gen_digraph(rely,table)

	print 'Done!'
