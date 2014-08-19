from socket import socket

class Benign():

    def execute(self, ip, port, flag_id='', token=''):

        error = 0
        error_msg = ''

        try:
            self.do_benign(ip, port)

        except Exception as e:
            error = 42
            error_msg = str(e)

        self.flag_id = ''
        self.token = ''
        self.error = error
        self.error_msg = error_msg

    def result(self):
        return {'FLAG_ID' : self.flag_id,
                'TOKEN' : self.token,
                'ERROR' : self.error,
                'ERROR_MSG' : self.error_msg,
               }

    def get_random_flag_id(self):
        import random
        import string
        username = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(16))
        return username

    def do_benign(self, ip, port):

        import pexpect
        from random import choice
        room_id = self.get_random_flag_id()

        children = [pexpect.spawn("nc {0} {1}".format(ip, port)) for i in range(3)]
        message_chunks = [['So then in eighth grade, I started going out with my first boyfriend,', 'Kyle, who was totally gorgeous, but then he moved to Indiana.', 'And Janis was, like, weirdly jealous of him.', 'Like, if I would blow her off to hang out with Kyle,', 'she\'d be like, Why didn\'t you call me back?"', 'And I\'d be like, "Why are you so obsessed with me?"', 'So then, for my birthday party, which was an all-girls pool party,', 'I was like, "Janis, I can\'t invite you, because I think you\'re a lesbian."', "I mean, I couldn't have a lesbian at my party."], ['There are gonna be girls there in their bathing suits.', 'I mean, right?', 'She was a lesbian.', 'So then her mom called my mom and started yelling at her.', 'It was so retarded.', 'And then she dropped out of school because no one would talk to her.', 'When she came back in the fall for high school,', 'all of her hair was cut off and she was totally weird,', "and now I guess she's on crack."], ['Oh, my God!', 'I love your skirt.', 'Where did you get it?', "It was my mom's in the 80's.", 'Vintage. So adorable.', 'Thanks.', 'That is the ugliest F-ing skirt', "I've ever seen.", 'Oh, my God, I love your bracelet.', 'Where did you get it?'], ["Oh, no, you can't like Aaron Samuels.", "That's Regina's ex-boyfriend.", 'They went out for a year.', 'Yeah, and then she was devastated when he broke up with her last summer.', 'I thought she dumped him for Shane Oman.', 'OK, irregardless.', 'Ex-boyfriends are just off-limits to friends.', "I mean, that's just, like, the rules of feminism.", "Don't worry. I'll never tell Regina what you said.", "It'll be our little secret."], ["So we'll see you tomorrow.", 'On Wednesdays, we wear pink.', 'Oh, my God!', 'OK, you have to do it, OK?', 'And then you have to tell me all', 'the horrible things that Regina says.', 'Regina seems sweet.', 'Regina George is not sweet.', "She's a scum-sucking road whore!", 'She ruined my life!', "She's fabulous, but she's evil."], ['Oh, God, and we gave you foot cream instead of face wash.', 'God! I am so sorry, Regina.', "Really, I don't know why I did it.", "I guess it's probably because", "I've got a big lesbian crush on you.", 'Suck on that!', 'Janis! Janis! Janis! Janis!', 'Regina!', "Regina, wait! I didn't mean for that to happen.", 'To find out that everyone hates me?', "I don't care.", 'Regina, please! Regina, stop!'], ['Regina George.', 'How do I even begin to explain Regina George?', 'Regina George is flawless.', 'She has two Fendi purses and a silver Lexus.', "I hear her hair's insured for $10,000", 'I hear she does car commercials.', 'In Japan.', 'Her favorite movie is Varsity blues.', 'One time, she met John Stamos on a plane.', 'And he told her she was pretty.', 'One time, she punched me in the face.', 'It was awesome.', 'She always looks fierce.', 'She always wins Spring Fling Queen.', 'Who cares?', 'I care.'], ["Laura, I don't hate you", "because you're fat.", "You're fat because I hate you.", 'I just wish we could all get along', 'like we used to in middle school.', 'I wish that I could bake a cake', 'made out of rainbows and smiles,', "and we'd all eat it and be happy.", "She doesn't even go here!", 'Do you even go to this school?', 'No. I just have a lot of feelings.', 'OK, go home.'], ["We're gonna get to the bottom of this right now.", "Maybe we're not in that book, because everybody likes us.", "And I don't wanna be punished for being well-liked.", "And I don't think my father, the inventor of Toaster Strudel,", 'would be too pleased to hear about this.', '"Made out with a hot dog"?', 'Oh, my God, that was one time!', '"Dawn Schweitzer has a huge ass"?', 'Who would write that?', "Who wouldn't write that?"], ["So if you're from Africa...why are you white?", "Oh, my God, Karen, you can't just", "ask people why they're white.", 'Could you give us some privacy for, like, one second?', 'Yeah, sure.', 'What are you doing?', "OK, you should just know that we don't do this a lot,", 'so this is, like, a really huge deal.', 'We wanna invite you to have lunch with us', 'every day for the rest of the week.', "Oh, it's OK...", 'Coolness.', "So we'll see you tomorrow.", 'On Wednesdays, we wear pink.']]

        #for index, child in enumerate(children):
        #    log = "mylog_{0}".format(index)
        #    child.logfile = open(log, "w")

        def type_message(child, msg):
            child.sendline(msg.strip())

        def everyone_cmd(msg):
            for child in children:
                child.sendline(msg)

        def everyone_expect(regex):
            for child in children:
                child.expect(regex)

        # Show up for work
        everyone_expect("Enter the number of a choice below:")
        everyone_cmd("1")

        # Enter room
        everyone_expect("Enter your room id:")
        everyone_cmd(room_id)

        # Mission starting
        everyone_expect(".*mission starting.*")
        #message_chunks = []
        #current_chunk = []
        #with open('mean_girls') as f:
        #    for line in f:
        #        if line != "\n":
        #            current_chunk.append(line.strip())
        #        else:
        #            message_chunks.append(current_chunk)
        #            current_chunk = []
        #    if current_chunk:
        #        message_chunks.append(current_chunk)
        #print message_chunks
        messages_to_send = choice(message_chunks)

        for message in messages_to_send:
            # Chooose a random agent
            type_message(choice(children), message)

        everyone_expect(messages_to_send[len(messages_to_send) - 1])         

