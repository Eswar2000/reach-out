import sys




def minDistance(dist, visited):
    min = sys.maxsize
    min_index = -1
    for ver in range(vertices):
        if dist[ver] < min and visited[ver] == False:
            min = dist[ver]
            min_index = ver
    return min_index

def backtrackMST(g,a):
    edgeList = []
    sum = 0
    print("Edges are : ", end="")
    for i in range(1, vertices):
        edgeList.append((a[i], i))
        print(a[i], i, sep="<->", end=" ")
        sum += g[i][a[i]]
    print("Total Length :", sum)


def prims(g):
    parentArr = [None] * vertices
    dist = [sys.maxsize] * vertices
    dist[0], parentArr[0] = 0, -1
    visited = [False] * vertices

    for _ in range(vertices):
        u = minDistance(dist, visited)
        if (u != -1):
            visited[u] = True
            for ver in range(vertices):
                if (g[u][ver] > 0 and visited[ver] == False and dist[ver] > g[u][ver]):
                    dist[ver] = g[u][ver]
                    parentArr[ver] = u
    print(dist)
    print(parentArr)
    backtrackMST(g,parentArr)

vertices = 5
g =  [[0, 2, 0, 6, 0],
     [2, 0, 3, 8, 5],
     [0, 3, 0, 0, 7],
     [6, 8, 0, 0, 9],
     [0, 5, 7, 9, 0]]

print(prims(g))