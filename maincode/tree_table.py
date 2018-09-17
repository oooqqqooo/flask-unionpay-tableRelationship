# -*- coding: utf-8 -*- 
'''解决表依赖横向画图箭头挡着表名的问题，'''
import matplotlib.pyplot as plt

decisionNode = dict(boxstyle="round4", fc="0.8")
leafNode = dict(boxstyle="round4", fc="0.8")
arrow_args = dict(arrowstyle="->",connectionstyle="arc3")
#上面三行代码定义文本框和箭头格式
#定义决策树决策结果的属性，用字典来定义，也可写作 decisionNode={boxstyle:'sawtooth',fc:'0.8'}
#其中boxstyle表示文本框类型，sawtooth是波浪型的，fc指的是注释框颜色的深度
#arrowstyle表示箭头的样式


''' 这里的annotate其实是增加标注的画图，参数xy=parentPt表示的标注位置，xytext=centerPt是文本位置'''
def plotNode(nodeTxt, centerPt, parentPt, nodeType,hasarrow=0):#该函数执行了实际的绘图功能
#nodeTxt指要显示的文本，centerPt指的是文本中心点，parentPt指向文本中心的点
    if hasarrow == 0:
        createPlot.ax1.annotate(nodeTxt, xy=parentPt,  xycoords='axes fraction',
                 xytext=centerPt, textcoords='axes fraction',
                 va="center", ha="right", bbox=nodeType, arrowprops=arrow_args )
    else:  ## 第二次调用plotNode，只画文本内容，以覆盖之前的箭头
        createPlot.ax1.annotate(nodeTxt, xy=parentPt,  xycoords='axes fraction',
             xytext=centerPt, textcoords='axes fraction',
             va="center", ha="right", bbox=nodeType)



#获取叶节点的数目
def getNumLeafs(myTree):
    numLeafs=0
    firstStr=list(myTree.keys())[0]#字典的第一个键，也就是树的第一个节点
    secondDict=myTree[firstStr]#这个键所对应的值，即该节点的所有子树。
    for key in secondDict.keys():
        if type(secondDict[key]).__name__=='dict':#测试节点的数据类型是否为字典
            numLeafs+=getNumLeafs(secondDict[key])#递归,如果是字典的话，继续遍历
        else:numLeafs+=1#如果不是字典型的话，说明是叶节点，则叶节点的数目加1
    return numLeafs
#获取树的层数
def getTreeDepth(myTree):#和上面的函数结果几乎一致
    maxDepth=0
    firstStr=list(myTree.keys())[0]
    secondDict=myTree[firstStr]
    for key in secondDict.keys():
        if type(secondDict[key]).__name__ == 'dict':
            thisDepth=1+getTreeDepth(secondDict[key])#递归
        else:thisDepth=1#一旦到达叶子节点将从递归调用中返回，并将计算深度加1
        if thisDepth>maxDepth:maxDepth=thisDepth
    return maxDepth

def plotTree(myTree,parentPt,nodeTxt,plotnode=0):
    numLeafs=getNumLeafs(myTree)#调用getNumLeafs（）函数计算叶子节点数目（宽度）
    depth=getTreeDepth(myTree)#调用getTreeDepth（），计算树的层数（深度）
    firstStr=list(myTree.keys())[0]
    cntrPt=(plotTree.xOff,plotTree.yOff+(1.0+float(numLeafs))/2.0/plotTree.totalW)#如果子节点较多，y值会
    #plotMidText(cntrPt,parentPt,nodeTxt)#调用 plotMidText（）函数，填充信息nodeTxt
    plotNode(firstStr,cntrPt,parentPt,decisionNode,plotnode)#调用plotNode（）函数，绘制箭头
    secondDict=myTree[firstStr]
    plotTree.xOff=plotTree.xOff+1.0/plotTree.totalD
    #因从左往右画，所以需要依次递减x的坐标值，plotTree.totalD表示存储树的深度
    for key in secondDict.keys():
        if type(secondDict[key]).__name__=='dict':
            #print(str(key))
            plotTree(secondDict[key],cntrPt,str(key),plotnode)#递归
        else:
            plotTree.yOff=plotTree.yOff+1.0/plotTree.totalW
            plotNode(secondDict[key],(plotTree.xOff,plotTree.yOff),cntrPt,leafNode,plotnode)
            #plotMidText((plotTree.xOff,plotTree.yOff),cntrPt,str(key))
    plotTree.xOff=plotTree.xOff-1.0/plotTree.totalD#h绘制完所有子节点后，增加全局变量x的偏移。

def createPlot(inTree,filename,layer,max_num,arrow):

	arrow_args["arrowstyle"]=arrow
	print layer,max_num
	width,heigth=image_config(layer,max_num)
	print '&&&',width,heigth
	fig=plt.figure(facecolor='white',figsize=(width,heigth))#绘图区域为白色
	fig.clf()#清空绘图区
	axprops = dict(xticks=[], yticks=[])#定义横纵坐标轴
	createPlot.ax1=plt.subplot(111,frameon=False,**axprops)
	#由全局变量createPlot.ax1定义一个绘图区，111表示一行一列的第一个，frameon表示边框,**axprops不显示刻度
	plotTree.totalW=float(getNumLeafs(inTree))
	plotTree.totalD=float(getTreeDepth(inTree))
	plotTree.yOff=-0.5/plotTree.totalW;plotTree.xOff=0.0;
	plotTree(inTree,(0.0,0.5),'',0)
	plotTree.yOff=-0.5/plotTree.totalW;plotTree.xOff=0.0;
	plotTree(inTree,(0.0,0.5),'',1)
	plt.savefig('pic/%s.png' % filename)
	#plt.show()

def image_config(layer,max_num):
    
	width = 4 + layer*4
	heigth = max_num
	return width,heigth
