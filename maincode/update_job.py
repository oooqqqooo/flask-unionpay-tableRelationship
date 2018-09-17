import pickle
import networkx as nx 

# job依赖的手动处理的更新
'''
有些表需要手动处理，提供接口更新网络的节点和边
'''

job = []; rely = [];opera = []
'''
add.txt测试用例
j1	['j2','j3']	a
j2	['j4','j9']	a
j4	['j5','j6','j7']	a
j5	['j8','j9','j10']	a
j4	['j5','j6','j7']	d
j1	['j3','j4']	m
'''
try:
    f1 = open('job_networkx.pkl','rb')
    DG = pickle.load(f1)
    f1.close()
except Exception as e:
    print '无原始依赖关系，初始化依赖！'
    DG = nx.DiGraph() 


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

with open('add.txt') as f:
    for i in f.readlines():
        line = i.strip().split('\t')
        edges = [(j,line[0])  for j in eval(line[1]) ]
        new_edges,nodes = edges_nodes(edges) 
        if line[2] == 'a':  # 'a'为增加操作
            DG.add_nodes_from(nodes) 
            DG.add_edges_from(new_edges) 
        elif line[2] == 'd':  #'d'为删除操作
            DG.remove_edges_from(new_edges)
        else:                  #'m'为修改操作  先删除节点的依赖关系，然后再进行增加操作
            DG.remove_edges_from([(j,line[0])  for j in list(DG.predecessors(line[0])) ])
            DG.add_nodes_from(nodes) 
            DG.add_edges_from(new_edges) 

with open('job_networkx.pkl','wb') as f:
    pickle.dump(DG,f)
