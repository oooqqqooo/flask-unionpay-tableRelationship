# -*- coding: utf-8 -*- 
import networkx as nx
import pickle
import matplotlib.pyplot as plt 
import tree_table
import os

#解析依赖和流向的关系，生成嵌套字典，如{'no surfacing': {0: 'no', 1: {'flippers': {0: 'no', 1: 'yes'}}, 3: 'maybe'}}，用于绘制树状图;
def parse(dic):
    num=0;d=[]
    for i in range(len(dic)):
        temp2={}
        for key,value in dic[i].items():
            temp={}
            if len(value)>0:
                for l in value:
                    temp[num] = l
                    num += 1
                temp2[key]=temp
        d.append(temp2)
    for j in range(len(d)-2,-1,-1):
        for key,value in d[j].items():
            for ke,va in value.items():
                try:
                    if va in d[j+1]:
                        d[j][key][ke]=dict([(va,d[j+1][va])])
                except TypeError:
                    pass
                
    return d[0]

def job_info(job):
    with open('job_info/tbl_sch_function_info.del') as f:
        index = 0
        for i in f.readlines():
            index += 1 
            if index==1:
                continue
            line =[j.strip(' ').strip('"') for j in i.strip().split(',')[:4]]
            if line[0]== job:
                return "y", str(job)+": "+line[3]+"/"+line[2]+'\n'
        return "n",""

#向上寻找依赖关系
def forward(g,pred,father,has_visited):
	newPred = [];dic={};pp=[]#pp 用于输出的顺序控制,使相邻层出现表的顺序一致
	for i in pred:
		temp=[]
		if i in has_visited:
			pp.append(temp)
			continue
		for j in g.predecessors(i):
			#1、原本是只要之前出现过的job或table就不再加入，但是这样会出现问题，a->b和c,,而b->c，这种情况b->c就会被忽略，因此需要修改代码
			#2、第二次修改，之前修改后大多数情况可以，但是当出现，a->b和c,,而b->d且c->d时d不再扩展，因此需要再次修改代码:增加一个变量has_visited，记录访问过的节点
			#if j not in father:
			has_visited.append(i)
			newPred.append(j)
			temp.append(j)
		dic[i]=temp
		pp.append(temp)
	for i in newPred:
		father.append(i)
	return father,newPred,dic,pred,pp,has_visited

#向下查看流向
def backward(g,succ,child,has_visited):
	newSucc = [];dic={};ss = []
	for i in succ:
		temp=[]
		if i in has_visited:
			ss.append(temp)
			continue
		for j in g.successors(i):
			#if j not in child:
			has_visited.append(i)
			newSucc.append(j)
			temp.append(j)
		dic[i]=temp
		ss.append(temp)
		for i in newSucc:
			child.append(i)
	return child,newSucc,dic,succ,ss,has_visited
	
#根据传入的参数查看表或job的依赖和流向，并进行图展示
def sub_draw_for(g,table,for_deepth=0):
    tag="n";s=""
    # pred是table的所有的父辈，succ是table的所有子辈
    pred =list(g.predecessors(table))
    for_deepth=int(for_deepth)
    #print type(pred)
    a = pred
    father = [i for i in pred];has_visited=[table]
    max_node_num=1  #记录每一层节点数的最大值
    layer=1  ##实际遍历层数
    if for_deepth>0:
        dic_ff=[];dic_ff.append(dict([(table,pred)]))
        s = s + '\n第1辈的依赖（直接依赖）：\n'+str(table)+' <-- '+str(pred)+'\n'
        if len(pred) > max_node_num:
            max_node_num=len(pred)
        for i in range(for_deepth-1):
            if len(pred)>0:
                curr_node_num=0##当前层节点数
                father,pred,dic_f,old_pred,pp,has_visited = forward(g,pred,father,has_visited)  #old_pred和pp用于输出顺序的控制
                if sum([len(k) for k in dic_f.values()])>0:  #没有依赖的字典中不一定为空，要判断字典中的value是不是都为空
                    s = s+'\n第'+str(i+2) +'辈的依赖：\n'
                    layer+=1
                de = []  #需要从字典中删除的元素
                for m in range(len(old_pred)):
                    if len(pp[m])>0:
                        s = s+str(old_pred[m])+' <-- '+str(pp[m])+'\n'
                        curr_node_num+=len(pp[m])
                if curr_node_num > max_node_num:
                    max_node_num=curr_node_num
                for key,value in dic_f.items():
                    if len(value)==0:
                        de.append(key)
                for d in de:
                    dic_f.pop(d)
                dic_ff.append(dic_f)
        ##所有依赖去重
        father_list=[]
        for j in father:
            if j not in father_list:
                father_list.append(j)
        s = s + '\n所有依赖：\n'+str(father_list)+'\n\n\n'
       
        #print layer,max_node_num
 
        pa_f = parse(dic_ff)
        if pa_f:
            if not os.path.exists( "static/job_images/%s_for_%d.png" %(table,for_deepth) ) :
                tree_table.createPlot(pa_f, "%s_for_%d" % (table,for_deepth), layer,max_node_num,"->")
            tag="y"

    return tag,s 

#根据传入的参数查看表或job的依赖和流向，并进行图展示
def sub_draw_back(g,table,back_deepth=0):
    tag="n";s=""
    # pred是table的所有的父辈，succ是table的所有子辈
    succ = list(g.successors(table))
    back_deepth=int(back_deepth)
    #print type(pred)
    b=succ   
    child = [i for i in succ];has_visited=[table]
    max_node_num=1  #记录每一层节点数的最大值
    layer=1 ##实际遍历层数
    if back_deepth>0:
        dic_bb=[];dic_bb.append(dict([(table,succ)]))  #dic_bb用于构建树状图的输入
        s = s +'第1代的流向（直接流向）：\n'+str(table)+' --> '+str(succ)+'\n'
        if len(succ) > max_node_num:
            max_node_num=len(succ)
        for j in range(back_deepth-1):
            if len(succ)>0:
                curr_node_num=0 ##当前层节点数
                child,succ,dic_b,old_succ,ss,has_visited= backward(g,succ,child,has_visited)
                if sum([len(k) for k in dic_b.values()])>0:
                    s = s +'\n第'+str(j+2)+'代的流向：\n'
                    layer+=1
                de = []
                for m in range(len(old_succ)):
                    if len(ss[m])>0:
                        s = s+str(old_succ[m])+' --> '+str(ss[m])+'\n'
                        curr_node_num+=len(ss[m])
                if curr_node_num > max_node_num:
                    max_node_num=curr_node_num
                for key,value in dic_b.items():
                    if len(value)==0:
                        de.append(key)
                for d in de:
                    dic_b.pop(d)
                dic_bb.append(dic_b)

        ##所有流向去重
        child_list=[]
        for j in child:
            if j not in child_list:
                child_list.append(j)
        s = s +'\n所有流向：\n'+str(child_list) +'\n'
        
        #print layer,max_node_num

        pa_b = parse(dic_bb)
        if pa_b:
            if not os.path.exists( "static/job_images/%s_back_%d.png" %(table,back_deepth) ) :
                tree_table.createPlot(pa_b, "%s_back_%d" % (table,back_deepth) ,layer,max_node_num,"<-")
            tag="y"

    return tag,s 

def get_job_relation(job_id,for_deepth,back_deepth,has_dim):
    if has_dim == 0:
        with open('table_networkx_nodim.pkl','rb') as f:
            DG = pickle.load(f)
    else:
        with open('table_networkx.pkl','rb') as f:
            DG = pickle.load(f)
    plt.switch_backend('agg')

    tag_info="n";tag_for="n";tag_back="n"
    try:
        tag_info,ret_info=job_info(job_id) 
        tag_for,ret_for=sub_draw_for(DG,job_id,for_deepth)
        tag_back,ret_back=sub_draw_back(DG,job_id,back_deepth)
        ret=ret_info+ret_for+ret_back
    except Exception as e:
        ret=e

    #ret=job_info(job_id)+sub_draw_for(DG,job_id,for_deepth)+sub_draw_back(DG,job_id,back_deepth)

    return tag_info,tag_for,tag_back,ret

if __name__ == '__main__':

	tag_info,tag_for,tag_back,ret = get_job_relation('dtdtrs_dtl_cups',10,10,0)
	f = open('result.txt','w')
	f.write(ret)
	f.close()

