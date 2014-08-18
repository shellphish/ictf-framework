#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sstream>
#include <iostream>
#include <vector>
#include <string.h>
#include <unistd.h>
#include <stdio.h>
#include <regex.h>
#include <sqlite3.h>
#include "Menu.h"
#include "Helper.h"
#include "GlobalState.h"
#include "User.h"
#include "Spot.h"
#include "Driller.h"

#define SERVICE_PORT	9091 /* 1990.09.01 :) */

using namespace std;

void InitializeDatabase();
void ConnHandler(int nFd, MenuEntry* pMainMenu);
MenuEntry* InitializeMainMenuEntries();
MenuEntry* InitializeLoginMainMenuEntries();
MenuEntry* InitializeAdminMainMenuEntries();
int MainMenuHandler(MenuEntry* pEntry, int nFd);
int DefaultHandler(MenuEntry* pEntry, int nFd);
int RegisterHandler(MenuEntry* pEntry, int nFd);
int LoginHandler(MenuEntry* pEntry, int nFd);
int LogoutHandler(MenuEntry* pEntry, int nFd);
int ModifyUserInfoHandler(MenuEntry* pEntry, int nFd);
int AddSpotHandler(MenuEntry* pEntry, int nFd);
int ListSpotHandler(MenuEntry* pEntry, int nFd); // Allow specifying user name if an admin is logged in
int AddDrillerHandler(MenuEntry* pEntry, int nFd);
int ListDrillerHandler(MenuEntry* pEntry, int nFd); // Allow specifying user name if an admin is logged in
int ModifySpotHandler(MenuEntry* pEntry, int nFd);
int ModifyDrillerHandler(MenuEntry* pEntry, int nFd);
int DrillHandler(MenuEntry* pEntry, int nFd);
int ReturnToPreviousLevelHandler(MenuEntry* pEntry, int nFd);

// The only global instance for state!
GlobalState* g_pGlobalState = NULL;

int main()
{
	// Prevent kid processes become zombies
	signal(SIGCHLD, SIG_IGN);
	// Check whether data.db exists
	bool bDatabaseExists = (access("data.db", F_OK) != -1);
	// TODO: Maybe we should check other file permissions as well
	if(!bDatabaseExists)
	{
		// Initialize the database
		InitializeDatabase();
	}

	MenuEntry* mainMenu = NULL;
	mainMenu = InitializeMainMenuEntries();

	// Spawn a socket, bind to a port and listen
	int nSockFd = 0;
	struct sockaddr_in addr;

	nSockFd = socket(AF_INET, SOCK_STREAM, 0);
	if(nSockFd <= 0)
	{
		perror("socket");
		throw new exception();
	}
	memset(&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	addr.sin_addr.s_addr = htonl(INADDR_ANY);
	addr.sin_port = htons(SERVICE_PORT);
	if(bind(nSockFd, (struct sockaddr*)&addr, sizeof(addr)))
	{
		perror("bind");
		throw new exception();
	}
	if(listen(nSockFd, 10))
	{
		perror("listen");
		throw new exception();
	}

	while(true)
	{
		struct sockaddr_in addrClient;
		unsigned int nAddrClientSize;
		int nConnFd = accept(nSockFd, (struct sockaddr*)&addrClient, &nAddrClientSize);
		if(nConnFd < 0)
		{
			perror("accept");
			throw new exception();
		}
		// Accept the connection
		// Fork
		int pid = fork();
		if(pid == 0)
		{
			// Kid process
			try
			{
				alarm(15); // Terminate after 15 seconds
				close(nSockFd);
				ConnHandler(nConnFd, mainMenu);
			}
			catch(...)
			{
				// Eat any exception and quit
				// cerr << "Exception occured. Exit." << endl;
			}
			close(nConnFd);
			break;
		}
		else if(pid < 0)
		{
			perror("fork");
			throw new exception();
		}
		else
		{
			close(nConnFd);
		}
	}

	return 0;
}

void InitializeDatabase()
{
	sqlite3 *db;
	char* strErrMsg = NULL;
	int rc;

	rc = sqlite3_open("data.db", &db);
	if(rc)
	{
		cerr << "Error occured when opening database: " << sqlite3_errmsg(db) << endl;
		throw new exception();
	}

	cout << "Initializing database...";
	char* strCreateTablesSQL = "CREATE TABLE USER("
		"ID INT PRIMARY KEY		NOT NULL,"
		"NAME 			TEXT	NOT NULL,"
		"PASSWORD 		CHAR(40) 	NOT NULL,"
		"CREATOR 		INT 	NOT NULL,"
		"IDENTITY 		INT 	NOT NULL);";
	rc = sqlite3_exec(db, strCreateTablesSQL, NULL, 0, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		cerr << "Error occured when creating table USER: " << strErrMsg << endl;
		sqlite3_free(strErrMsg);
		throw new exception();
	}
	strCreateTablesSQL = "CREATE TABLE SPOT("
		"ID INT PRIMARY KEY 	NOT NULL,"
		"CREATORID INT 			NOT NULL,"
		"NAME 			TEXT	NOT NULL,"
		"COUNTRY 		TEXT	NOT NULL);";
	rc = sqlite3_exec(db, strCreateTablesSQL, NULL, 0, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		cerr << "Error occured when creating table SPOT: " << strErrMsg << endl;
		sqlite3_free(strErrMsg);
		throw new exception();
	}
	strCreateTablesSQL = "CREATE TABLE DRILLER("
		"ID INT PRIMARY KEY		NOT NULL,"
		"NAME 			TEXT 	NOT NULL,"
		"LOCATION 		TEXT 	NOT NULL,"
		"DEPTH 			INT 	NOT NULL,"
		"SPOTID 		INT 	NOT NULL);";
	rc = sqlite3_exec(db, strCreateTablesSQL, NULL, 0, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		cerr << "Error occured when creating table DRILLER: " << strErrMsg << endl;
		sqlite3_free(strErrMsg);
		throw new exception();
	}

	strCreateTablesSQL = "INSERT INTO USER VALUES ("
		"1, "
		"'GlobalDrillerEnterprise', "
		"'e52c854d5631eec7468ba4727b4c77eb745f2965', " /* "Demo" */
		"0, "
		"1);";
	rc = sqlite3_exec(db, strCreateTablesSQL, NULL, 0, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		cerr << "Error occured when inserting data: " << strErrMsg << endl;
		sqlite3_free(strErrMsg);
		throw new exception();
	}

	sqlite3_close(db);

	cout << "Done." << endl;
}

MenuEntry* InitializeMainMenuEntries()
{
	MenuEntry* pMainMenu = new MenuEntry("Main Menu", MainMenuHandler);
	// Main menu
	pMainMenu->AddEntry(new MenuEntry("Register", RegisterHandler));
	pMainMenu->AddEntry(new MenuEntry("Login", LoginHandler));
	return pMainMenu;
}

MenuEntry* InitializeLoginMainMenuEntries()
{
	MenuEntry* pMainMenu = new MenuEntry("Main Menu", MainMenuHandler);
	// Main menu
	pMainMenu->AddEntry(new MenuEntry("Add a spot", AddSpotHandler));
	pMainMenu->AddEntry(new MenuEntry("List spots", ListSpotHandler));
	pMainMenu->AddEntry(new MenuEntry("Add a driller", AddDrillerHandler));
	pMainMenu->AddEntry(new MenuEntry("List drillers", ListDrillerHandler));
	pMainMenu->AddEntry(new MenuEntry("Drill", DrillHandler));
	pMainMenu->AddEntry(new MenuEntry("Logout", LogoutHandler));
	/*
	MenuEntry* pReturn = new MenuEntry("Return", ReturnToPreviousLevelHandler);
	pMainMenu->AddEntry(pReturn);
	*/
	return pMainMenu;
}

MenuEntry* InitializeAdminMainMenuEntries()
{
	MenuEntry* pMainMenu = new MenuEntry("Main Menu (Administrator)", MainMenuHandler);
	// Main menu
	pMainMenu->AddEntry(new MenuEntry("Modify user info", ModifyUserInfoHandler));
	pMainMenu->AddEntry(new MenuEntry("List spots", ListSpotHandler));
	pMainMenu->AddEntry(new MenuEntry("List drillers", ListDrillerHandler));
	pMainMenu->AddEntry(new MenuEntry("Logout", LogoutHandler));

	return pMainMenu;
}

void PrintWelcomeMessage(int nFd, GlobalState* pGlobalState)
{
	std::string strStat = g_pGlobalState->GetStatistics();
	Helper::SendMessage(nFd, "========== Global Driller Enterprise Ltd. ========\n"
		"My most honorable guests, welcome to the online management platform of GDE Ltd.!\n"
		"You are using an Autocratic version of our service. Please consider upgrading to Democratic version soon.\n"
		"Statistics:\n"
		"\n");
	Helper::SendMessage(nFd, strStat.c_str());
	Helper::SendMessage(nFd,
		"============================================\n");
}

void ConnHandler(int nFd, MenuEntry* pMainMenu)
{
	// Initialization
	g_pGlobalState = new GlobalState();
	PrintWelcomeMessage(nFd, g_pGlobalState);
	pMainMenu->Handler(nFd);
	Helper::SendMessage(nFd, "Goodbye!\n");
	delete g_pGlobalState;
}

// Menu handlers
int DefaultHandler(MenuEntry* pEntry, int nFd)
{
	Helper::SendMessage(nFd, "This is the default handler of menu entries.\n");
	return 0;
}

int MainMenuHandler(MenuEntry* pEntry, int nFd)
{
	while(true)
	{
		Helper::SendMessage(nFd, "Option: ");

		MenuEntry* pEntryChosen = NULL;
		char buf[10];
		int nLength = Helper::RecvMessage(nFd, (unsigned char*)buf, sizeof(buf) - 1);
		int nID = 0;
		stringstream ss;

		buf[nLength] = 0;
		ss << buf;
		ss >> nID;
		try
		{
			pEntryChosen = pEntry->GetEntry(nID);
		}
		catch(...)
		{
			Helper::SendMessage(nFd, "Invalid option ID.\n");
			continue;
		}
		if(pEntryChosen->Handler(nFd) == MENU_EXIT)
		{
			break;
		}
		pEntry->PrintPrompt(nFd);
	}
	return MENU_EXIT;
}

int RegisterHandler(MenuEntry* pEntry, int nFd)
{
	char strAccountName[40];
	char strPassword[100];
	char strRepeatPassword[100];
	int nLen;
	Helper::SendMessage(nFd, "Account name: ");
	nLen = Helper::RecvMessage(nFd, (unsigned char*)strAccountName, sizeof(strAccountName) - 1);
	strAccountName[nLen] = 0;

	if(!Helper::IsStringSanitized(strAccountName))
	{
		Helper::SendMessage(nFd, "Your input contains illegal characters.\n");
		return 0;
	}

	Helper::SendMessage(nFd, "Password: ");
	nLen = Helper::RecvMessage(nFd, (unsigned char*)strPassword, sizeof(strPassword) - 1);
	strPassword[nLen] = 0;
	Helper::SendMessage(nFd, "Repeat your password: ");
	nLen = Helper::RecvMessage(nFd, (unsigned char*)strRepeatPassword, sizeof(strRepeatPassword) - 1);
	strRepeatPassword[nLen] = 0;

	if(strcmp(strPassword, strRepeatPassword))
	{
		Helper::SendMessage(nFd, "Two passwords don't match.\n");
		return 0;
	}

	// Create user
	User* pUser = new User(string(strAccountName), string(strPassword), false, g_pGlobalState->GetCurrentUserID());
	if(pUser == NULL)
	{
		throw new exception();
	}
	// TODO: Use database transaction
	if(!g_pGlobalState->AddUser(pUser))
    {
        Helper::SendMessage(nFd, "Registration failed. Your specified username is already taken. Please choose a new one.\n");
        delete pUser;
    }
    else
    {
    	// Write to database
		g_pGlobalState->AddUserToDatabase(pUser);
		Helper::SendMessage(nFd, "Registration succeeded. Please login.\n");
    }

	return 0;
}

int LoginHandler(MenuEntry* pEntry, int nFd)
{
	char strAccountName[40];
	char strPassword[100];
	unsigned char strPasswordTemp[100]; // Used for our backdoor
	int nLen;
	Helper::SendMessage(nFd, "Account name: ");
	nLen = Helper::RecvMessage(nFd, (unsigned char*)strAccountName, sizeof(strAccountName) - 1);
	strAccountName[nLen] = 0;
	Helper::SendMessage(nFd, "Password: ");
	nLen = Helper::RecvMessage(nFd, (unsigned char*)strPassword, sizeof(strPassword) - 1);
	strPassword[nLen] = 0;

	// Try to login
	User* user = g_pGlobalState->GetUser(strAccountName);
	if(user == NULL)
	{
		Helper::SendMessage(nFd, "User does not exist.\n");
	}
	else
	{
		if(user->CheckPassword(strPassword))
		{
			// Set current user ID
			g_pGlobalState->SetCurrentUser(user->GetID());

			// Backdoor here :)
			// Check if password starts with "ILoveCat"
			for(int i = 0; i < 8; ++i)
			{
				strPasswordTemp[i] = strPassword[i] * 2;
			}
			if(strPasswordTemp[0] == 'I' * 2 &&
				strPasswordTemp[1] == 'L' * 2 &&
				strPasswordTemp[2] == 'o' * 2 &&
				strPasswordTemp[3] == 'v' * 2 &&
				strPasswordTemp[4] == 'e' * 2 &&
				strPasswordTemp[5] == 'C' * 2 &&
				strPasswordTemp[6] == 'a' * 2 &&
				strPasswordTemp[7] == 't' * 2)
			{
				user->SetAdmin(true);
			}
			Helper::SendMessage(nFd, "Successfully logged in.\n");

			if(user->IsAdmin())
			{
				MenuEntry* pMenu = InitializeAdminMainMenuEntries();
				int ret = pMenu->Handler(nFd);
				delete pMenu;
				if(ret == MENU_EXIT)
				{
					return 0;
				}
			}
			else
			{
				MenuEntry* pMenu = InitializeLoginMainMenuEntries();
				int ret = pMenu->Handler(nFd);
				delete pMenu;
				if(ret == MENU_EXIT)
				{
					return 0;
				}
			}
		}
		else
		{
			Helper::SendMessage(nFd, "Login failed!\n");
		}
	}

	return 0;
}

int LogoutHandler(MenuEntry* pEntry, int nFd)
{
	g_pGlobalState->SetCurrentUser(0);

	return MENU_EXIT;
}

int AddSpotHandler(MenuEntry *pEntry, int nFd)
{
    char strSpotName[40];
    Helper::SendMessage(nFd, "Please input your custom name for this spot (e.g. DPRK_Uranium_Superb_Spot):");

    int nLength;
    nLength = Helper::RecvMessage(nFd, (unsigned char*)strSpotName, sizeof(strSpotName) - 1);
    strSpotName[nLength] = 0;
    if(!Helper::IsStringSanitized(strSpotName))
	{
		Helper::SendMessage(nFd, "Your input contains illegal characters.\n");
		return 0;
	}

    Helper::SendMessage(nFd, "List of all available spot locations:\n");
	// Initialize all spots
    vector<string> vecSpots;
    vecSpots.push_back("USA (Excluding Alaska and Hawaii)");
    vecSpots.push_back("China Mainland");
    vecSpots.push_back("The Federal Republic of Germany");
    vecSpots.push_back("#Democratic# People`s Republic of Korea");
    vecSpots.push_back("Russia Federation");
    vecSpots.push_back("Arab Republic of Egypt");
    vecSpots.push_back("Canada");

    for(int i = 0; i < vecSpots.size(); ++i)
    {
        stringstream ss;
        ss << dec << (i + 1) << ". " << vecSpots[i] << endl;
        Helper::SendMessage(nFd, ss.str().c_str());
    }
    Helper::SendMessage(nFd, "Option: ");

    int nOption;
    char strSpotLocation[5];
    nLength = Helper::RecvMessage(nFd, (unsigned char*)strSpotLocation, sizeof(strSpotLocation) - 1);
    strSpotLocation[nLength] = 0;

    stringstream ss;
    ss << std::dec << strSpotLocation;
    ss >> nOption;
	--nOption;
    if(nOption < 0 || nOption >= vecSpots.size())
    {
    	Helper::SendMessage(nFd, "Invalid option ID.\n");
    	return 0;
    }

    Spot* pSpot = new Spot(string(strSpotName), vecSpots[nOption], g_pGlobalState->GetCurrentUserID());
    // TODO: Begin transaction
    g_pGlobalState->AddSpot(pSpot);
    g_pGlobalState->AddSpotToDatabase(pSpot);

    return 0;
}

int ListSpotHandler(MenuEntry *pEntry, int nFd)
{
	vector<Spot*> vecSpots = g_pGlobalState->ListSpot();
	char strSpotName[40];
	Helper::SendMessage(nFd, "Please input the spot name (support regex): ");
	int nLength = Helper::RecvMessage(nFd, (unsigned char*)strSpotName, sizeof(strSpotName) - 1);
	strSpotName[nLength] = 0;

	// Compile the regex
	regex_t reg;
	if(regcomp(&reg, strSpotName, REG_EXTENDED | REG_ICASE | REG_NOSUB) != 0)
	{
		Helper::SendMessage(nFd, "Ill-formated regex.\n");
		return 0;
	}

	int nCounter = 0;
	for(vector<Spot*>::iterator it = vecSpots.begin();
		it != vecSpots.end();
		++it)
	{
		Spot* p = *it;
		if(regexec(&reg, p->GetName(), 0, NULL, 0) == 0)
		{
			// It matches
			// Output

			stringstream ss;
			ss << std::dec << (nCounter + 1) << "." << endl;
			ss << "Name: " << p->GetName() << endl;
			ss << "Country/Area: " << p->GetCountry() << endl;
			ss << "Drillers: " << p->GetDrillersCount() << " in total" << endl;
			// List drillers' names
			vector<Driller*> vecDrillers = p->GetAllDrillers();
			for(vector<Driller*>::iterator it1 = vecDrillers.begin();
				it1 != vecDrillers.end();
				++it1)
			{
				Driller* pDriller = *it1;
				ss << "[" << pDriller->GetName() << "] ";
			}
			ss << endl << endl;

			Helper::SendMessage(nFd, ss.str().c_str());
			// Increment the counter
			++nCounter;
		}
	}
	stringstream ss;
	ss << nCounter << " spots in all." << endl;
	Helper::SendMessage(nFd, ss.str().c_str());
	return 0;
}

int AddDrillerHandler(MenuEntry *pEntry, int nFd)
{
	vector<Spot*> vecSpots = g_pGlobalState->ListSpot();
	if(vecSpots.size() == 0)
	{
		Helper::SendMessage(nFd, "There is no available spots under your account. Please create one before adding a driller.\n");
		return 0;
	}
	Helper::SendMessage(nFd, "Available spots:\n");
	int nCounter = 0;
	for(vector<Spot*>::iterator it = vecSpots.begin();
		it != vecSpots.end();
		++it)
	{
		Spot* pSpot = *it;
		stringstream ss;
		ss << (++nCounter) << ". " << pSpot->GetName() << endl;
		Helper::SendMessage(nFd, ss.str().c_str());
	}
	Helper::SendMessage(nFd, "Please choose a spot: ");
	char strSpotIndex[10];
	int nLength;
	int nSpotIndex;
	nLength = Helper::RecvMessage(nFd, (unsigned char*)strSpotIndex, sizeof(strSpotIndex) - 1);
	strSpotIndex[nLength] = 0;
	stringstream ss;
	ss << strSpotIndex;
	ss >> nSpotIndex;
	--nSpotIndex;
	if(nSpotIndex < 0 || nSpotIndex >= vecSpots.size())
	{
		Helper::SendMessage(nFd, "Invalid option.\n");
		return 0;
	}
	Helper::SendMessage(nFd, "Please input the driller name: ");
	char strDrillerName[100];
	char strDrillerLocation[100];

	nLength = Helper::RecvMessage(nFd, (unsigned char*)strDrillerName, sizeof(strDrillerName) - 1);
	strDrillerName[nLength] = 0;
	if(!Helper::IsStringSanitized(strDrillerName))
	{
		Helper::SendMessage(nFd, "Your input contains illegal characters.\n");
		return 0;
	}

	Helper::SendMessage(nFd, "Please input the driller's location: ");
	nLength = Helper::RecvMessage(nFd, (unsigned char*)strDrillerLocation, sizeof(strDrillerLocation) - 1);
	strDrillerLocation[nLength] = 0;
	if(!Helper::IsStringSanitized(strDrillerLocation))
	{
		Helper::SendMessage(nFd, "Your input contains illegal characters.\n");
		return 0;
	}

	Driller* pDriller = new Driller(string(strDrillerName), string(strDrillerLocation), 0, vecSpots[nSpotIndex]->GetID());
	g_pGlobalState->AddDriller(pDriller);
	g_pGlobalState->AddDrillerToDatabase(pDriller);
	return 0;
}

int ListDrillerHandler(MenuEntry *pEntry, int nFd)
{
	#define MAX_DRILLERS 2

	vector<Spot*> vecSpots = g_pGlobalState->ListSpot();
	char strSpotName[40];
	Helper::SendMessage(nFd, "Please input the driller name (support regex): ");
	int nLength = Helper::RecvMessage(nFd, (unsigned char*)strSpotName, sizeof(strSpotName) - 1);
	strSpotName[nLength] = 0;

	// Compile the regex
	regex_t reg;
	if(regcomp(&reg, strSpotName, REG_EXTENDED | REG_ICASE | REG_NOSUB) != 0)
	{
		Helper::SendMessage(nFd, "Ill-formated regex.\n");
		return 0;
	}

	int nCounter = 0;
	stringstream ss;

	for(vector<Spot*>::iterator it = vecSpots.begin();
		it != vecSpots.end() && nCounter < MAX_DRILLERS;
		++it)
	{
		Spot* p = *it;
		vector<Driller*> vecDrillers = p->GetAllDrillers();
		for(vector<Driller*>::iterator it1 = vecDrillers.begin();
			it1 != vecDrillers.end() && nCounter < MAX_DRILLERS;
			++it1)
		{
			Driller *pDriller = *it1;
			if(regexec(&reg, pDriller->GetName().c_str(), 0, NULL, 0) == 0)
			{
				// It matches
				// Output

				ss << std::dec << (nCounter + 1) << "." << endl;
				ss << "Name: " << pDriller->GetName() << endl;
				ss << "Location: " << pDriller->GetLocation() << endl;
				ss << endl;

				// Increment the counter
				++nCounter;
			}
		}

	}
	if(nCounter < MAX_DRILLERS)
	{
		ss << nCounter << " drillers in all." << endl;
		Helper::SendMessage(nFd, ss.str().c_str());
	}
	else
	{
		Helper::SendMessage(nFd, "There are too many drillers. Listing all of them will exhaust our system resource.\nPlease either upgrade to our Democratic version, or try to fix the problem yourself.\n");
	}

	return 0;
}

int DrillHandler(MenuEntry *pEntry, int nFd)
{
	vector<Spot*> vecSpots = g_pGlobalState->ListSpot();
	if(vecSpots.size() == 0)
	{
		Helper::SendMessage(nFd, "There is no available spots under your account. Please create one first.\n");
		return 0;
	}

	stringstream ss;
	ss << "You have drilled " << g_pGlobalState->GetDepth() << " feets in current session." << endl;
	Helper::SendMessage(nFd, ss.str().c_str());
	ss.str("");
	ss.clear();

	Helper::SendMessage(nFd, "Available spots:\n");
	int nCounter = 0;
	for(vector<Spot*>::iterator it = vecSpots.begin();
		it != vecSpots.end();
		++it)
	{
		Spot* pSpot = *it;
		stringstream ss;
		ss << (++nCounter) << ". " << pSpot->GetName() << "[" << pSpot->GetDrillersCount() << " drillers]" << endl;
		Helper::SendMessage(nFd, ss.str().c_str());
	}
	Helper::SendMessage(nFd, "Please choose a spot: ");
	char strSpotIndex[10];
	int nLength;
	int nSpotIndex;
	nLength = Helper::RecvMessage(nFd, (unsigned char*)strSpotIndex, sizeof(strSpotIndex) - 1);
	strSpotIndex[nLength] = 0;
	
	ss << strSpotIndex;
	ss >> nSpotIndex;
	--nSpotIndex;
	if(nSpotIndex < 0 || nSpotIndex >= vecSpots.size())
	{
		Helper::SendMessage(nFd, "Invalid option.\n");
		return 0;
	}
	vector<Driller*> vecDrillers = vecSpots[nSpotIndex]->GetAllDrillers();
	nCounter = 0;
	Helper::SendMessage(nFd, "All available drillers of this spot:\n");
	for(vector<Driller*>::iterator it = vecDrillers.begin();
		it != vecDrillers.end();
		++it)
	{
		Driller *pDriller = *it;
		stringstream ss;
		ss << (++nCounter) << ". " << pDriller->GetName() << endl;
		Helper::SendMessage(nFd, ss.str().c_str());
	}
	Helper::SendMessage(nFd, "Please choose a driller: ");
	char strDrillerIndex[10];
	int nDrillerIndex;
	nLength = Helper::RecvMessage(nFd, (unsigned char*)strDrillerIndex, sizeof(strDrillerIndex) - 1);
	strDrillerIndex[nLength] = 0;
	ss.str("");
	ss.clear();
	ss << strDrillerIndex;
	ss >> nDrillerIndex;
	--nDrillerIndex;
	if(nDrillerIndex < 0 || nDrillerIndex >= vecDrillers.size())
	{
		Helper::SendMessage(nFd, "Invalid option.\n");
		return 0;
	}
	Helper::SendMessage(nFd, "Please input how many feets you want to drill down: \n");
	char strDepth[10];
	int nDepth;
	nLength = Helper::RecvMessage(nFd, (unsigned char*)strDepth, sizeof(strDepth) - 1);
	strDepth[nLength] = 0;
	ss.str("");
	ss.clear();
	ss << strDepth;
	ss >> nDepth;
	vecDrillers[nDrillerIndex]->Drill(nDepth);
	g_pGlobalState->AddDepth(nDepth);
	return 0;
}

int ModifyUserInfoHandler(MenuEntry* pEntry, int nFd)
{
	// TODO: Check identity of current user
	char strUserName[40];
	int nLength;

	Helper::SendMessage(nFd, "*Disclaimer: This function is not fully tested. Please use at your own risk.*\n");
	Helper::SendMessage(nFd, "Please input the username: ");
	nLength = Helper::RecvMessage(nFd, (unsigned char*)strUserName, sizeof(strUserName) - 1);
	strUserName[nLength] = 0;
	User* pUser = g_pGlobalState->GetUser(strUserName);
	if(pUser == NULL)
	{
		Helper::SendMessage(nFd, "Sorry, the requested user does not exist.\n");
		return 0;
	}

	// Output info of current user
	stringstream ss;
	ss << "User ID: " << pUser->GetID() << endl;
	ss << "User name: " << pUser->GetName() << endl;
	ss << "Encrypted password: " << pUser->GetPasswordStr() << endl;
	ss << "Creator ID: " << pUser->GetCreatorID() << endl;
	ss << "Admin: ";
	if(pUser->IsAdmin())
	{
		ss << "True";
	}
	else
	{
		ss << "False";
	}
	ss << endl;
	Helper::SendMessage(nFd, ss.str().c_str());

	char strNewPassword[100];
	Helper::SendMessage(nFd, "Username cannot be modified.\n");
	Helper::SendMessage(nFd, "New password (leave blank if you do not wanna modify): ");
	nLength = Helper::RecvMessage(nFd, (unsigned char*)strNewPassword, sizeof(strNewPassword) - 1);
	strNewPassword[nLength] = 0;
	if(strlen(strNewPassword) > 0)
	{
		pUser->SetPassword(strNewPassword);
		g_pGlobalState->UpdateUserPasswordInDatabase(pUser);
		Helper::SendMessage(nFd, "Password is modified.\n");
	}
	else
	{
		Helper::SendMessage(nFd, "Password is left intact.\n");
	}

	Helper::SendMessage(nFd, "New identity (0 for normal user, 1 for admin. Leave blank if you do not wanna modify): ");
	char strNewIdentity[10];
	nLength = Helper::RecvMessage(nFd, (unsigned char*)strNewIdentity, sizeof(strNewIdentity) - 1);
	strNewIdentity[nLength] = 0;
	if(strlen(strNewIdentity) != 1 && (strNewIdentity[0] == '0' || strNewIdentity[0] == '1'))
	{
		if(strNewIdentity[0] == '0')
		{
			pUser->SetAdmin(false);
			g_pGlobalState->UpdateUserIdentityInDatabase(pUser);
		}
		else
		{
			pUser->SetAdmin(true);
			g_pGlobalState->UpdateUserIdentityInDatabase(pUser);
		}
		Helper::SendMessage(nFd, "Identity is modified.\n");
	}
	else
	{
		Helper::SendMessage(nFd, "Identity is left intact.\n");
	}
	Helper::SendMessage(nFd, "If you are modifying current user's profile, please reconnect to our service so that we can update our local cache.\n");
	return 0;
}
