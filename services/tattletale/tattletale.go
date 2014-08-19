// Force people to play game of go manually against bot, after winning that
// round they get matched with faster bot, either beat him... or realize you can
// match with yourself in the 2nd round. oops... this isn't relevant anymore. Thanks Kyle >:|.
package main

import (
	"bufio"
    "math/rand"
	"fmt"
	"io"
	"log"
	"net"
	"runtime"
	"strings"
	"sync"
	"text/tabwriter"
	"time"
)

const (
	ListenAddr  = ":13007"
	TurnTimeout = 15 * time.Second
	RoomTimeout = 2000 * time.Second
	JoinTimeout = 30 * time.Second
	WaitTimeout = 20 * time.Second
	NumPlayers  = 3
)

type FStore struct {
	datab map[string][]string
	mu    sync.RWMutex
}

func (s *FStore) Get(key string) []string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.datab[key]
}
func (s *FStore) Set(key string, value []string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	_, present := s.datab[key]
	if present {
		return false
	}
	s.datab[key] = value
	return true
}
func (s *FStore) Delete(key string) {
	s.mu.Lock()
	delete(s.datab, key)
	s.mu.Unlock()
}
func (s *FStore) Update(key string, value []string) {
	s.mu.Lock()
	delete(s.datab, key)
	s.datab[key] = value
	s.mu.Unlock()
}
func NewDB() *FStore {
	return &FStore{
		datab: make(map[string][]string),
	}
}

var db = NewDB()

func main() {
	runtime.GOMAXPROCS(runtime.NumCPU())

	rand.Seed(time.Now().UnixNano())
	l, err := net.Listen("tcp", ListenAddr)
	if err != nil {
		log.Fatal(err)
	}
	for {
		c, err := l.Accept()
		if err != nil {
			log.Fatal(err)
		}
		go lobby(c)
	}
}

func lobby(c io.ReadWriteCloser) {
	printMenu(c)

	var cmd int
	_, err := fmt.Fscanln(c, &cmd)
	if err != nil {
		c.Close()
		return
	}

	switch cmd {
	case 1:
		match(c)
	case 2:
		setflag(c)
	case 3:
		getflag(c)
	default:
		c.Close()
		return
	}
}

func printMenu(c io.Writer) {
	fmt.Fprintln(c, "Enter the number of a choice below:")
	fmt.Fprintln(c, "    1) Show up for work ")
	fmt.Fprintln(c, "    2) Create target room")
	fmt.Fprintln(c, "    3) Get target room value")
}

// Thread safe map for storing clients entering rooms. Each room_id has its own
// channel to queue up new connections.
var cStore = NewCStore()

// Thread safe map implementation for connection management
// for the flag_id, password, flag DB. Design from talk by Andrew
// Gerrand: http://www.youtube.com/watch?feature=player_embedded&v=2-pPAvqyluI
type CStore struct {
	rooms map[string]chan io.ReadWriteCloser
	mu    sync.RWMutex
}

func (s *CStore) Get(key string) chan io.ReadWriteCloser {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.rooms[key]
}
func (s *CStore) Set(key string, room chan io.ReadWriteCloser) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	_, present := s.rooms[key]
	if present {
		return false
	}
	s.rooms[key] = room
	return true
}
func (s *CStore) Delete(key string) {
	s.mu.Lock()
	delete(s.rooms, key)
	s.mu.Unlock()
}
func NewCStore() *CStore {
	return &CStore{
		rooms: make(map[string]chan io.ReadWriteCloser),
	}
}

func getroomid(c io.ReadWriter) (string, error) {
	fmt.Fprintln(c, "You arrive at work. A monolithic building rises before you. Try act normal. ")
	fmt.Fprintln(c, "(Hint: This is your flag_id and can be anything if you are testing)\n")
	fmt.Fprintln(c, "Enter your room id:")
	var cmd string
	_, err := fmt.Fscanln(c, &cmd)
	if err != nil {
		return cmd, fmt.Errorf("%v", "Invalid roomid")
	}
	return cmd, nil
}
func match(c io.ReadWriteCloser) {
	roomid, err := getroomid(c)
	if err != nil {
		fmt.Fprintln(c, "Invalid RoomID")
		c.Close()
		return
	} else if roomid == "641A" {
		fmt.Fprintln(c, "This room has not the data you are looking for. Get out!")
		c.Close()
		return
	}
	queue := make(chan io.ReadWriteCloser)
	// if queue doesn't exist create room
	if cStore.Set(roomid, queue) {
		log.Println("Launch Chat")
		go groupchat(queue, roomid)
	} else if queue = cStore.Get(roomid); queue == nil {
		fmt.Fprintln(c, "Room ID not yet available")
		c.Close()
		return
	}

	// enter queue
	select {
	case queue <- c:
	case <-time.After(WaitTimeout):
		fmt.Fprintln(c, "Room Full!")
		log.Println("waitlist timeout")
		c.Close()
	}
}

type File struct {
    Name string
	Size  int
	Value int
    qty int //used for knapsack, always 1
}

type Leaker struct {
	conn      io.ReadWriteCloser
	Files     map[string]File
	Bandwidth int
    isDone    bool
}

type GameState map[string]*Leaker

type Snowden struct {
    Init bool //starts false until he is messaged first time
    Endtoken chan int //guards one person entering end room
    Files map[string][]File
    SnowdenSolution int
    Roomid string
}
func (s *Snowden) String() string {
    return "E.Snowden"
}

func groupchat(queue <-chan io.ReadWriteCloser, roomid string) {
	// collect connections
	conns := make([]io.ReadWriteCloser, 0, NumPlayers)
	for i := 0; i < NumPlayers; i++ {
		//conns[i] = <-queue
		select {
		case c := <-queue:
			conns = append(conns, c)
            broadcast(conns, fmt.Sprintf("       --> | Agent%v has joined #%v", i, roomid))
		case <-time.After(JoinTimeout):
			broadcast(conns, fmt.Sprintf("Not everyone showed up for work: Goodbye!", i))
	        cStore.Delete(roomid)
			for i := range conns {
				conns[i].Close()
			}
			log.Printf("Room never filled: %v\n", roomid)
            return
		}
	}
	// free roomid and use of queue
	cStore.Delete(roomid)
	broadcast(conns, "      * -- | Everyone has arrived, mission starting...")
	broadcast(conns, "      * -- | Ask for help to get familiar around here")

    // Initialize game state
    snowden := &Snowden {
        Init: false,
        Endtoken: make(chan int, 1),
        Files: make(map[string][]File, NumPlayers + 1),
        Roomid: roomid,
    }
    snowden.Endtoken <- 1
	gamestate := make(map[string]*Leaker, NumPlayers+2)
	for i := 0; i < NumPlayers; i++ {
        id := newID(i)
		gamestate[id] = &Leaker{
			conn:  conns[i],
			Files: make(map[string]File),
			isDone: false,
		}
        snowden.Files[id] = []File{}
	}
	knapsackInit(gamestate)

    // set target solution
    snowden.SnowdenSolution = solveknapsack(gamestate)


	// start input worker per player
	errc := make(chan error, 1)
	inpc := make(chan *Message, 10)
	for id, v := range gamestate {
		go sendparser(v.conn, inpc, errc, id)
	}
	go gamedispatch(gamestate, snowden, inpc, errc)

	// wait for first error to close game
	if err := <-errc; err != nil {
		log.Println(err)
	}
	// close clients
	for i := range conns {
		conns[i].Close()
	}
	log.Printf("room shutdown: %v\n", roomid)

}

const (
	NumFiles = 15
)

var names = []string{"Agent0", "Agent1", "Agent2", "Agent3", "Agent4"}

func newID(i int) string {
	return names[i]
}

var wordlist = []string{
	"RadicalPornEnthusiasts", "SIGINT", "BoundlessInformant",
	"TorStinks", "GCHQ", "EgoGiraffe", "PRISM", "641A", "Verizon",
	"PsyOps", "LOVEINT", "QuantumCookie", "FoxAcid", "G20", "BULLRUN",
    "RONIN", "Upstream", "MasteringTheInternet", "IllegalDataCollectionAndYou",
}
var extlist = []string{".ppt", ".docx", ".doc"}

func newFileName(player, file int) string {
	index := NumFiles*player + file
	word := index / len(extlist)
	ext := index % len(extlist)
	return wordlist[word] + extlist[ext]

	/* random ppt files
	   b := make([]byte, 10)
	   rand.Read(b)
	   en := base32.StdEncoding
	   d := make([]byte, en.EncodedLen(len(b)))
	   en.Encode(d, b)
	   return string(d) + ".ppt"                 
	*/
}
const (
    sizerange = 3000
    sizeoffset = 200
    valuerange = 90
    valueoffset = 10
    smallmod = 5
    bigmod = 5
)

func initFiles(fmap map[string]File, playernum int) (filesum int) {
    filesum = 0
	for i := 0; i < NumFiles; i++ {
        name := newFileName(playernum, i)
        size := (rand.Int() % sizerange) + sizeoffset
        filesum += size
		fmap[name] = File{
			Size:  size,
			Value: (rand.Int() % valuerange) + valueoffset,
            Name: name,
            qty: 1,
		}
	}
    return filesum
}

func knapsackInit(s GameState) {
	i := 0
    var remaining = 0
    var luckyagent = rand.Int() % NumPlayers
    var luckyid string
    var luckysum int

	for id, v := range s {
        filesum := initFiles(v.Files, i)
        if i == luckyagent {
            luckyid = id
            luckysum = filesum
            i++
            continue
        } else {
		    v.Bandwidth = (filesum * smallmod) / 10 //avoiding floats here with
            remaining += filesum - v.Bandwidth
        }
		i++
	}
    s[luckyid].Bandwidth =  luckysum + (bigmod*remaining) / 10

}

type Message struct {
	To   string
	From string
	Cmd  string
	Msg  string
}

//Commands!
const (
	LIST = "/list"
	WHO  = "/look"
	MSG  = "/msg"
	SEND = "/send"
	CAST = "/all"
	HELP = "/help"
)

func sendparser(c io.ReadWriter, input chan<- *Message, errc chan<- error, id string) {
	scanner := bufio.NewScanner(c)

	for scanner.Scan() {
		var to, msg, cmd string
		s := strings.SplitN(scanner.Text(), " ", 3)
		switch strings.ToLower(s[0]) {
		case MSG:
			cmd = MSG
			if len(s) > 2 {
				to = s[1]
				msg = s[2]
			} else {
				fmt.Fprintln(c, "  Error -- | '/msg' has 2 arguments")
				continue
			}
		case SEND:
			cmd = SEND
			if len(s) > 2 {
				to = s[1]
				msg = s[2]
			} else {
				fmt.Fprintln(c, "  Error -- | '/send' has 2 arguments")
				continue
			}
		case LIST:
			cmd = LIST
			msg = ""
			to = id
		case WHO:
			cmd = WHO
			msg = ""
			to = id
		case HELP:
			cmd = HELP
			msg = ""
			to = id
		default:
			msg = scanner.Text()
			to = "*"
			cmd = CAST
		}
		message := &Message{
			To:   to,
			From: id,
			Msg:  msg,
			Cmd:  cmd,
		}
		input <- message //send to dispatch
	}
	if err := scanner.Err(); err != nil {
		errc <- err
	} else {
		errc <- io.EOF //apparently EOF is not an scanner err
	}
}

func broadcast(conns []io.ReadWriteCloser, msg string) {
	for i := range conns {
		fmt.Fprintln(conns[i], msg)
	}
}

func broadcastmsg(g GameState, msg *Message) {
	for id, v := range g {
		if id != msg.From {
		    fmt.Fprintf(v.conn, "    %v | %v\n", msg.From, msg.Msg)
		} else if id == msg.From {
		    fmt.Fprintf(v.conn, "    %v | %v\n", msg.From, msg.Msg)
		}
	}
}

func sendmsg(g GameState, msg *Message) {
	if _, ok := g[msg.To]; ok {
		fmt.Fprintf(g[msg.To].conn, "    msg -- | *msg to %v: %v\n", msg.To, msg.Msg)
		sender := msg.From
		fmt.Fprintf(g[sender].conn, "    msg -- | *msg to %v: %v\n", msg.To, msg.Msg)
	} else {
		fmt.Fprintf(g[msg.From].conn, "  Error | Invalid Recipient ID\n")
	}

}
func listfiles(g GameState, msg *Message) {
	if v, ok := g[msg.From]; ok {
		w := new(tabwriter.Writer)
		w.Init(v.conn, 4, 0, 1, ' ', tabwriter.AlignRight)
        fmt.Fprintf(w, "   list -- | Remaining Bandwidth: %v KB\n", g[msg.From].Bandwidth)
        fmt.Fprintf(w, "  list -- |\tName\tSize\tSecrecy Value\t\n")
		for k, v := range v.Files {
			fmt.Fprintf(w, "  list -- |\t%v\t%vKB\t%v\t\n", k, v.Size, v.Value)
		}
		w.Flush()
	} else {
		log.Fatal("invaled sender ID")
	}
}
func help(g GameState, msg *Message) {
	p := "   help -- | "
	if v, ok := g[msg.From]; ok {
		fmt.Fprintln(v.conn, p, "[game desription]")
		fmt.Fprintln(v.conn, p)
		fmt.Fprintln(v.conn, p, "Usage:", p)
		fmt.Fprintln(v.conn, p)
		fmt.Fprintln(v.conn, p, "\t /[cmd] [arguments]")
		fmt.Fprintln(v.conn, p)
		fmt.Fprintln(v.conn, p, "The commands are:")
		fmt.Fprintln(v.conn, p)
		fmt.Fprintln(v.conn, p, "\t/msg [to] [text]         send message to coworker")
		fmt.Fprintln(v.conn, p, "\t/list                    look at files you have access to")
		fmt.Fprintln(v.conn, p, "\t/send [to] [filename]    mv file to coworker")
		fmt.Fprintln(v.conn, p, "\t/look                    show coworkers")
	} else {
		log.Fatal("invalid sender id")
	}
}
func sendfile(g GameState, s *Snowden, msg *Message) {
	sender := g[msg.From]
	// file exists?
	if file, ok := sender.Files[msg.Msg]; ok {

        // recipient exists?
if v, ok := g[msg.To]; ok {
            //delete
	        delete(sender.Files, msg.Msg)
			//add file
			v.Files[msg.Msg] = file
            fmt.Fprintf(v.conn, "    send -- | *Received File: %v(%v) from %v\n", msg.Msg, file.Size, msg.From)
            fmt.Fprintf(sender.conn, "    send -- | *Sent File: %v to %v \n", msg.Msg, msg.To)
		} else {
			fmt.Fprintf(g[msg.From].conn, "  Error -- | Invalid Recipient ID\n")
		}

	} else {
		fmt.Fprintf(g[msg.From].conn, "  Error -- | Invalid File ID\n")
	}

}
func who(g GameState, s *Snowden, msg *Message) {
	if v, ok := g[msg.From]; ok {
        pre := "   look -- | "
		fmt.Fprintln(v.conn, pre,  "You look at your co-workers' nametags:")
		fmt.Fprintln(v.conn, pre)
		for id, _ := range g {
			fmt.Fprintln(v.conn, pre , "\t", id)
		}
        fmt.Fprintln(v.conn, pre, "\t", s.String())
	} else {
		log.Fatal("recieved invalid sender ID")
	}

}

//Game commands: SendFile to player, sendfile to snowden, list files (director)
func gamedispatch(g GameState, s *Snowden, input <-chan *Message, errc chan<- error) {
	var msg *Message
	for {
		select {
		case msg = <-input:
			switch msg.Cmd {
			case CAST:
				broadcastmsg(g, msg)
			case MSG:
                if msg.To == s.String() {
                    snowdendispatch(g, s, msg, errc)
                } else {
				    sendmsg(g, msg)
                }
			case LIST:
				listfiles(g, msg)
			case SEND:
                if msg.To == s.String() {
                    snowdendispatch(g, s, msg, errc)
                } else {
				    sendfile(g, s, msg)
                }
			case HELP:
				help(g, msg)
			case WHO:
				who(g, s, msg)
			default:
			}
		case <-time.After(RoomTimeout):
			errc <- fmt.Errorf("Group Timeout")
		}
	}
}

func snowdendispatch(g GameState, s *Snowden, msg *Message, errc chan<- error) {
    if !s.Init && msg.Cmd == MSG {
        sendGreeting(g, s , msg)
        s.Init = true
    } else if msg.Cmd == MSG {
        fmt.Fprintf(g[msg.From].conn, "    msg -- | *msg to %v: %v\n", msg.To, msg.Msg)
        if strings.ToLower(msg.Msg) == "done" {
            g[msg.From].isDone = true

            alldone := true
            for _, v := range g {
                if !v.isDone {
                    alldone = false
                }
            }
            if alldone {
                select {
                case <-s.Endtoken:
                    endgame(g, s, msg, errc)
                default: return
                }
            } else  {
	            fmt.Fprintf(g[msg.From].conn, " %v | Waiting for the rest of your team...\n", s.String())
            }

        } else {
	        fmt.Fprintf(g[msg.From].conn, " %v | Are you done yet?\n", s.String())
        }
    } else if msg.Cmd == SEND {
        transfer(g, s, msg, errc)
    }
}
func transfer(g GameState, s *Snowden, msg *Message, errc chan<- error) {
    sender := g[msg.From]
	// file exists?
	if file, ok := sender.Files[msg.Msg]; ok {
		delete(sender.Files, msg.Msg)
        flist := s.Files[msg.From]
        // enough bandwidth?
        g[msg.From].Bandwidth -= file.Size
        if sender.Bandwidth < 0 {
            //Exceeded Limit! You've been caught!
            text := []string{"You get flagged for transfering too much data away from your group. Turns out"}
            text = append(text, "that security exercise wasn't authorized, Oops. You and your buddy E.Snowden are")
            text = append(text, "sent to your employee's correctional training facility. I'm sure they'll be very")
            text = append(text, "gentle and that you will surely see the light of day again...")
            for i := range(text) {
                fmt.Fprintf(sender.conn, "    End -- | %v\n", text[i])
            }
            errc <- fmt.Errorf("Transfer Quota Exceeded")
            return
        } else {
			//add file
            //flist = append(flist, file)
            s.Files[msg.From] = append(flist,file)
            fmt.Fprintf(sender.conn, "   send -- | *Sent File: %v to %v *\n", msg.Msg, msg.To)
        }
	} else {
		fmt.Fprintf(g[msg.From].conn, "  Error -- | Invalid File ID\n")
	}
}
func endgame(g GameState, s *Snowden, msg *Message, errc chan<- error) {
    var sum = 0
    w := new(tabwriter.Writer)
    w.Init(g[msg.From].conn, 4, 0, 1, ' ', tabwriter.AlignRight)
    for id, filelist := range s.Files {
        fmt.Fprintf(w, "    End -- | exfiltrated files from %v:\n", id)
        if len(filelist) != 0 {
		    fmt.Fprintln(w, " End -- | \tName\tSize\tSecrecy Value\t")
        }
        for i := range filelist {
            f := filelist[i]
			fmt.Fprintf(w, "  End -- | \t%v\t%vKB\t%v\t\n", f.Name, f.Size, f.Value)
            sum += f.Value
		}
    }
    fmt.Fprintf(w, "    End -- | Total Document Impact Score: %v \n", sum)
    if sum > s.SnowdenSolution {
        //win get flag
        fmt.Fprintf(w, "    End -- | \n")
        fmt.Fprintf(w, "    End -- | The total value of you documents has exceeded E.Snowden's target goal of :%v\n", s.SnowdenSolution)
        fmt.Fprintf(w, "    End -- | Congratulations! E.Snowden has sucessfully achieved asylum due to the impact of\n")
        fmt.Fprintf(w, "    End -- | his leaks. Here is a signed message from him to prove you helped him along the\n")
        fmt.Fprintf(w, "    End -- | way. I think your boss will want this: ")
        entry := db.Get(s.Roomid)
	    if entry == nil {
            fmt.Fprintf(w, "    End -- | hmm, it seems your room_id(flag_id) does not have an associated flag ZDI\n")
            fmt.Fprintf(w, "    End -- | will be sure to make you exfiltrate documents from the correct target\n")
		    log.Println("Documents exfiltrated successfully, but roomid not set prior")
	    } else {
		    fmt.Fprintln(w, entry[1])
		    log.Println("Documents exfiltrated successfully!")
	    }
    } else {
        fmt.Fprintf(w, "    End -- | \n")
        fmt.Fprintf(w, "    End -- | The total value of you documents must exceed E.Snowden's target goal of: %v\n", s.SnowdenSolution)
        fmt.Fprintf(w, "    End -- | It seems the political impact of the exfiltrated documents is less then\n")
        fmt.Fprintf(w, "    End -- | Desirable. As a result the leakers have trouble seeking asylum in other\n")
        fmt.Fprintf(w, "    End -- | countries and you all get sent back to your employer.\n")
        fmt.Fprintf(w, "    End -- | \n")
        fmt.Fprintf(w, "    End -- | You and your friends are swiftly tortured by the righteous hand of justice.\n")
        fmt.Fprintf(w, "    End -- | Better luck next life!\n")
    }
    w.Flush()
    errc <- fmt.Errorf("Game Finished")
}

type Solution struct {
    v, w int
    qty []int
}

func solveknapsack(g GameState) int {
    value := 0
    for _ , fileset := range g {
        files := make([]File, 0)
        //convert map to list
        for _, file :=  range fileset.Files {
            files = append(files, file)
        }
        v, _, s := choose(fileset.Bandwidth, len(files) - 1, make(map[string]*Solution), files)

        //fmt.Println("Solution: ", id)
        for _, t := range s {
            if t > 0 {
                //fmt.Printf("  %d of %d %s\n", t, files[i].qty, files[i].Name)
            }
        }
        //fmt.Printf("Value: %d; bandwidth: %d\n", v, w)  
        value += v
    }
    return value
}
func choose(bandwidth, pos int, cache map[string]*Solution, files []File) (int, int, []int) {

    if pos < 0 || bandwidth <= 0 {
        return 0, 0, make([]int, len(files))
    }

    str := fmt.Sprintf("%d,%d", bandwidth, pos)
    if s, ok := cache[str]; ok {
        return s.v, s.w, s.qty
    }

    best_v, best_i, best_w, best_sol := 0, 0, 0, []int(nil)

    for i := 0; i * files[pos].Size <= bandwidth && i <= files[pos].qty; i++ {
        v, w, sol := choose(bandwidth - i * files[pos].Size, pos - 1, cache, files)
        v += i * files[pos].Value
        if v > best_v {
            best_i, best_v, best_w, best_sol = i, v, w, sol
        }
    }

    taken := make([]int, len(files))
    copy(taken, best_sol)
    taken[pos] = best_i
    v, w := best_v, best_w + best_i * files[pos].Size

    cache[str] = &Solution{v, w, taken}

    return v, w, taken
}

func sendGreeting(g GameState, s *Snowden, m *Message) {
    msg := []string{"Psst, hey there. I'm going to need your help if we want to exfiltrate these"}
    msg = append(msg, "documents. You have access to files I don't.")
    msg = append(msg, "")
    msg = append(msg, "You each have a list of secret files you have access to. Within your group you")
    msg = append(msg, "can freely send files to each other for further analysis.  However, to get these")
    msg = append(msg, "files outside your group, you must transfer them onto your super secure USB")
    msg = append(msg, "drive (You know, for working at home and stuff) to send them to me. However,")
    msg = append(msg, "when sending files to me you deduct from you total transfer quota. The")
    msg = append(msg, "department doesn't want you working *too* hard at home you know.")
    msg = append(msg, "")
    msg = append(msg, "So, since you all can freely transfer among yourselves, it'd be great if you")
    msg = append(msg, "could kindly team up to use your transfer quotas wisely. I need you all to send")
    msg = append(msg, "me your files without exceeding your quota. Please optimize your transfers by")
    msg = append(msg, "the political impact it will create. The file's security clearance is a good")
    msg = append(msg, "metric to go by for that. Thanks!")
    msg = append(msg, "")
    msg = append(msg, "When each of you is finished sending files, send me the message 'done'. I'll")
    msg = append(msg, "I'll need to here this from all of you before I consider your submission.")
    for i := range msg {
        fmt.Fprintf(g[m.From].conn, " %v | %v\n", s.String(), msg[i])
    }
}
func setflag(c io.ReadWriteCloser) {
	defer c.Close()

	var flag_id string
    fmt.Fprintln(c, "room_id: ")
	_, err := fmt.Fscanln(c, &flag_id)
	if err != nil {
		return
	}
	var cookie string
    fmt.Fprintln(c, "auth_token: ")
	_, err = fmt.Fscanln(c, &cookie)
	if err != nil {
		return
	}
	var flag string
    fmt.Fprintln(c, "flag: ")
	_, err = fmt.Fscanln(c, &flag)
	if err != nil {
		return
	}

	if db.Set(flag_id, []string{cookie, flag}) {
		fmt.Fprintln(c, "set_flag flag_set")
		log.Println("setflag: flag set")
	} else if cookie == db.Get(flag_id)[0] {
		db.Update(flag_id, []string{cookie, flag})
        fmt.Fprintln(c, "setflag: flag_updated")
		log.Println("setflag: flag updated")
	} else {
        fmt.Fprintln(c, "setflag: flag_update_auth_fail")
		log.Println("setflag: auth fail")
	}
}

func getflag(c io.ReadWriteCloser) {
	defer c.Close()
	var flag_id string
    fmt.Fprintln(c, "flag_id: ")
	_, err := fmt.Fscanln(c, &flag_id)
	if err != nil {
		return
	}
	var cookie string
    fmt.Fprintln(c, "token_id: ")
	_, err = fmt.Fscanln(c, &cookie)
	if err != nil {
		return
	}
	entry := db.Get(flag_id)
	if entry == nil {
        fmt.Fprintln(c, "flagval: no_entry_exists")
		log.Println("getflag: request for non-existant entry")
	} else if cookie == entry[0] {
        fmt.Fprintln(c, "flagval:", entry[1])
		log.Println("getflag: got")
	} else {
        fmt.Fprintln(c, "flagval: getflag_auth_fail")
		log.Println("getflag: auth fail")
    }
	return
}
