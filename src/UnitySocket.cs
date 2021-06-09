using System;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

public class UnitySocket : MonoBehaviour
{
    static Socket listener;
    private CancellationTokenSource source;
    public ManualResetEvent allDone;

    public static readonly int PORT = 8080;
    public static readonly int WAITTIME = 1;


    UnitySocket()
    {
        source = new CancellationTokenSource();
        allDone = new ManualResetEvent(false);
    }

    // Start is called before the first frame update
    async void Start()
    {
        await Task.Run(() => ListenEvents(source.Token));   
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    private void ListenEvents(CancellationToken token)
    {

        
        IPHostEntry ipHostInfo = Dns.GetHostEntry(Dns.GetHostName());
        IPAddress ipAddress = ipHostInfo.AddressList.FirstOrDefault(ip => ip.AddressFamily == AddressFamily.InterNetwork);
        IPEndPoint localEndPoint = new IPEndPoint(ipAddress, PORT);

         
        listener = new Socket(ipAddress.AddressFamily, SocketType.Stream, ProtocolType.Tcp);

         
        try
        {
            listener.Bind(localEndPoint);
            listener.Listen(10);

             
            while (!token.IsCancellationRequested)
            {
                allDone.Reset();

                print("Waiting for a connection... host :" + ipAddress.MapToIPv4().ToString() + " port : " + PORT);
                listener.BeginAccept(new AsyncCallback(AcceptCallback),listener);

                while(!token.IsCancellationRequested)
                {
                    if (allDone.WaitOne(WAITTIME))
                    {
                        break;
                    }
                }
      
            }

        }
        catch (Exception e)
        {
            print(e.ToString());
        }
    }

    void AcceptCallback(IAsyncResult ar)
    {  
        Socket listener = (Socket)ar.AsyncState;
        Socket handler = listener.EndAccept(ar);
 
        allDone.Set();
  
        StateObject state = new StateObject();
        state.workSocket = handler;
        handler.BeginReceive(state.buffer, 0, StateObject.BufferSize, 0, new AsyncCallback(ReadCallback), state);
    }

    void ReadCallback(IAsyncResult ar)
    {
        StateObject state = (StateObject)ar.AsyncState;
        Socket handler = state.workSocket;

        int read = handler.EndReceive(ar);
  
        if (read > 0)
        {
            state.receivedData.Append(Encoding.ASCII.GetString(state.buffer, 0, read));
            handler.BeginReceive(state.buffer, 0, StateObject.BufferSize, 0, new AsyncCallback(ReadCallback), state);
        }
        else
        {
            if (state.receivedData.Length > 1)
            {
                string content = state.receivedData.ToString();
                print($"Read {content.Length} bytes from socket.\n Data : {content}");
                SetArray(content);
            }
            handler.Close();
        }
    }

    private void SetArray(string data)
    {
        string[] arrayData = data.Split(',');
        for (int i=0; i < arrayData.Length -1 ; i++) 
        {
            print(arrayData[i]);
        }

        //Convert to 2d array

        //int j = 0;
        //int arrayRow = 3;
        //int arrayColumn = 2;
        //string[,] newArray = new string[arrayRow, arrayColumn];

        //for (int y = 0; y < arrayRow; y++)
        //{
        //    print("for loop 1");
        //    for (int x = 0; x < arrayColumn; x++)
        //    {
        //        print("for loop 2");
        //        newArray[y, x] = arrayData[j];
        //        j++; 
        //    }
        //}

        //int rowLength = newArray.GetLength(0);
        //int colLength = newArray.GetLength(1);

        //for (int r = 0; r < rowLength; r++)
        //{
        //    for (int c = 0; c < colLength; c++)
        //    {
        //        print("row: " + r + " column: " + c + " is: " + newArray[r,c]);
        //    }

        //}
    }

    private void OnDestroy()
    {
        source.Cancel();
    }

    public class StateObject
    {
        public Socket workSocket = null;
        public const int BufferSize = 1024;
        public byte[] buffer = new byte[BufferSize];
        public StringBuilder receivedData = new StringBuilder();
    }
}
