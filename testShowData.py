import plotly.offline as py
import plotly.graph_objs as go
import pymysql

if __name__ == '__main__':
    comm = pymysql.connect(host='10.10.11.189', port=3338, user='root', password='123456', db='test1')
    cursor = comm.cursor()
    # cursor.execute(
    #     "select date_format(t1.`time`, '%Y-%m-%d %H-%i') time,round(avg(t1.`numeric` - (t2.`numeric`+ 0.05414851615450247)) * 1000000, 2) data from test1 t1 inner join test1 t2 on date_format(t1.`time`, '%Y-%m-%d %H-%i') = date_format(t2.`time`, '%Y-%m-%d %H-%i') where t1.type = 4 and t2.type = 2124 group by time;")
    #
    cursor.execute(
        "select date_format(time, '%Y-%m-%d %H-%i') times, round(avg(`numeric`),6) from test1 where type = 4 group by times")
    data = cursor.fetchall()
    x1 = []
    y1 = []
    for x, y in data:
        x1.append(x)
        y1.append(y)
    trace1 = go.Scatter(
        x=x1,
        y=y1,
        mode='lines+markers',
        name='lines+markers'
    )
    cursor.execute(
        "select date_format(time, '%Y-%m-%d %H-%i') times, round(avg(`numeric`),6) from test1 where type = 2124 group by times")
    data = cursor.fetchall()
    x1 = []
    y1 = []
    for x, y in data:
        x1.append(x)
        y1.append(y)
    trace2 = go.Scatter(
        x=x1,
        y=y1,
        mode='lines',
        name='lines'
    )
    data = [trace1, trace2]
    py.plot(data)
