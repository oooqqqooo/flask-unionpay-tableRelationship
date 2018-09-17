# -*- coding: utf-8 -*- 
import pickle
import networkx as nx 

'''
有些表需要手动处理，提供接口更新网络的节点和边
'''

'''
add.txt测试用例
t1	['t2','t3']	a 
t2	['t4','t9']	a
t4	['t5','t6','t7']	a
t5	['t8','t9','t10']	a
t4	['t5','t6','t7']	d
t1	['t3','t4']	m
'''
try:
    f1 = open('table_networkx.pkl','rb')
    DG = pickle.load(f1)
    f2 =  open('table_networkx_nodim.pkl','rb')
    DG2 = pickle.load(f2)
    f1.close()
    f2.close()
except Exception as e:
	print '无原始依赖关系，初始化依赖！'
	DG = nx.DiGraph() 
	DG2 = nx.DiGraph()

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

with open('update.txt') as f:
    for i in f.readlines():
        line = i.strip().split('\t')
        edges_nodim = [(j.strip('hbkdb.'),line[0].strip('hbkdb.')) for j in eval(line[1]) if 'dim' not in str(j)and 'dim' not in line[0]]
        edges = [(j.strip('hbkdb.'),line[0].strip('hbkdb.'))  for j in eval(line[1]) ]
        new_edges,nodes = edges_nodes(edges) 
        new_edges_nodim,nodes_nodim = edges_nodes(edges_nodim)
        if line[2] == 'a':  # 'a'为增加操作
            DG.add_nodes_from(nodes) 
            DG.add_edges_from(new_edges) 
            DG2.add_nodes_from(nodes_nodim) 
            DG2.add_edges_from(new_edges_nodim) 
        elif line[2] == 'd':  #'d'为删除操作
            DG.remove_edges_from(new_edges)
            DG2.remove_edges_from(new_edges_nodim) 
        else:                  #'m'为修改操作  先删除节点的依赖关系，然后再进行增加操作
            DG.remove_edges_from([(j,line[0])  for j in list(DG.predecessors(line[0])) ])
            DG2.remove_edges_from([(j,line[0])  for j in list(DG2.predecessors(line[0])) ])
            DG.add_nodes_from(nodes) 
            DG.add_edges_from(new_edges) 
            DG2.add_nodes_from(nodes_nodim) 
            DG2.add_edges_from(new_edges_nodim)

with open('table_networkx.pkl','wb') as f:
    pickle.dump(DG,f)

with open('table_networkx_nodim.pkl','wb') as f1:
    pickle.dump(DG2,f1)