#include <vector>
#include <sstream>
#include <iostream>
#include <iomanip>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include "User.h"
#include "Spot.h"
#include "Driller.h"
#include "GlobalState.h"

GlobalState::GlobalState()
{
	// Initialize RNG
	srand(time(NULL));

	// We randomize the heap base address a little bit
	// to make it a little bit harder :D
	// Randomly generate lottery numbers

	this->m_nLotteryNumber1 = ((unsigned int)rand() << 16) | rand();
	this->m_nLotteryNumber2 = ((unsigned int)rand() << 16) | rand();
	// Allocate some buffers
	std::vector<void*> vecTemp;
	for(int i = 0; i < this->m_nLotteryNumber1 % 199091; ++i)
	{
		vecTemp.push_back(malloc(4));	
	}

	// Initialization
	this->m_nDrillersCount = 0;
	this->m_nGlobalDrillingDepth = 0;
	this->m_nCurrentUserID = 0;
	this->m_pvecUsers = new std::vector<User*>();
	this->m_pvecSpots = new std::vector<Spot*>();
	this->m_pDb = NULL;

	// Free all those allocated buffers
	for(std::vector<void*>::iterator it = vecTemp.begin();
		it != vecTemp.end();
		++it)
	{
		free(*it);
	}

	this->InitializeFromDatabase();
}

GlobalState::~GlobalState()
{
	for(std::vector<User*>::iterator it = this->m_pvecUsers->begin();
		it != this->m_pvecUsers->end();
		++it)
	{
		delete(*it);
	}
	for(std::vector<Spot*>::iterator it = this->m_pvecSpots->begin();
		it != this->m_pvecSpots->end();
		++it)
	{
		delete(*it);
	}
	delete this->m_pvecUsers;
	delete this->m_pvecSpots;
	if(this->m_pDb != NULL)
	{
		sqlite3_close(this->m_pDb);
	}
}

User* GlobalState::GetCurrentUser()
{
	int nID = this->GetCurrentUserID();
	for(std::vector<User*>::iterator it = this->m_pvecUsers->begin();
		it != this->m_pvecUsers->end();
		++it)
	{
		User* pUser = *it;
		if(pUser->GetID() == nID)
		{
			return pUser;
		}
	}
	return NULL;
}

static int GetMaxUserIDCallback(void* pGlobalState_, int argc, char** argv, char** azColName)
{
	GlobalState* pGlobalState = (GlobalState*)pGlobalState_;
	// TODO: Assert argc == 1
	std::stringstream ss;
	if(argv[0] != NULL)
	{
		ss << argv[0];
		int nMaxID;
		ss >> nMaxID;
		pGlobalState->SetMaxUserID(nMaxID);
	}
	return 0;
}

void GlobalState::SetMaxUserID(int nMaxUserID)
{
	this->m_nMaxUserID = nMaxUserID;
}

int GlobalState::GetMaxUserID()
{
	// Initialize
	this->m_nMaxUserID = 0;
	// TODO: assert(this->m_pDb) != NULL
	char* strSql = "SELECT Max(ID) FROM USER;";
	char* strErrMsg;
	int rc = sqlite3_exec(this->m_pDb, strSql, GetMaxUserIDCallback, (void*)this, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		std::cerr << "SQL error occurred when querying USER table: " << strErrMsg << std::endl;
		sqlite3_free(strErrMsg);
		throw new std::exception();
	}
	return this->m_nMaxUserID;
}

static int GetMaxSpotIDCallback(void* pGlobalState_, int argc, char** argv, char** azColName)
{
	GlobalState* pGlobalState = (GlobalState*)pGlobalState_;
	// TODO: Assert argc == 1
	std::stringstream ss;
	if(argv[0] != NULL)
	{
		ss << argv[0];
		int nMaxID;
		ss >> nMaxID;
		pGlobalState->SetMaxSpotID(nMaxID);
	}
	return 0;
}

void GlobalState::SetMaxSpotID(int nMaxSpotID)
{
	this->m_nMaxSpotID = nMaxSpotID;
}

int GlobalState::GetMaxSpotID()
{
	// Initialize
	this->m_nMaxSpotID = 0;
	// TODO: assert(this->m_pDb) != NULL
	char* strSql = "SELECT Max(ID) FROM SPOT;";
	char* strErrMsg;
	int rc = sqlite3_exec(this->m_pDb, strSql, GetMaxSpotIDCallback, (void*)this, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		std::cerr << "SQL error occurred when querying SPOT table: " << strErrMsg << std::endl;
		sqlite3_free(strErrMsg);
		throw new std::exception();
	}
	return this->m_nMaxSpotID;
}

static int GetMaxDrillerIDCallback(void* pGlobalState_, int argc, char** argv, char** azColName)
{
	GlobalState* pGlobalState = (GlobalState*)pGlobalState_;
	// TODO: Assert argc == 1
	std::stringstream ss;
	if(argv[0] != NULL)
	{
		ss << argv[0];
		int nMaxID;
		ss >> nMaxID;
		pGlobalState->SetMaxDrillerID(nMaxID);
	}
	return 0;
}

void GlobalState::SetMaxDrillerID(int nMaxID)
{
	this->m_nMaxDrillerID = nMaxID;
}

int GlobalState::GetMaxDrillerID()
{
	// Initialize
	this->m_nMaxDrillerID = 0;
	// TODO: assert(this->m_pDb) != NULL
	char* strSql = "SELECT Max(ID) FROM DRILLER;";
	char* strErrMsg;
	int rc = sqlite3_exec(this->m_pDb, strSql, GetMaxDrillerIDCallback, (void*)this, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		std::cerr << "SQL error occurred when querying DRILLER table: " << strErrMsg << std::endl;
		sqlite3_free(strErrMsg);
		throw new std::exception();
	}
	return this->m_nMaxDrillerID;
}

static int ReadUserCallback(void* pGlobalState_, int argc, char** argv, char** azColName)
{
	GlobalState* pGlobalState = (GlobalState*)pGlobalState_;
	// TODO: assert(argc == 5)
	char* strID = argv[0];
	char* strAccountName = argv[1];
	char* strHashedPassword = argv[2];
	char* strCreatorID = argv[3];
	char* strIdentity = argv[4];
	int nID, nCreatorID, nIdentity;
	std::stringstream ss;
	ss << strID;
	ss >> nID;
	ss.str("");
	ss.clear();
	ss << strCreatorID;
	ss >> nCreatorID;
	ss.str("");
	ss.clear();
	ss << strIdentity;
	ss >> nIdentity;
	ss.str("");
	ss.clear();
	User* pUser = new User(std::string(strAccountName), std::string(strHashedPassword), (nIdentity != 0), nID, nCreatorID);
	pGlobalState->AddUser(pUser);
	return 0;
}

static int ReadSpotCallback(void* pGlobalState_, int argc, char** argv, char** azColName)
{
	GlobalState* pGlobalState = (GlobalState*)pGlobalState_;
	// TODO: assert(argc == 4)
	char* strID = argv[0];
	char* strName = argv[2];
	char* strCreatorID = argv[1];
	char* strCountry = argv[3];
	int nID, nCreatorID;
	std::stringstream ss;
	ss << strID;
	ss >> nID;
	ss.str("");
	ss.clear();
	ss << strCreatorID;
	ss >> nCreatorID;
	ss.str("");
	ss.clear();
	Spot* pSpot = new Spot(std::string(strName), std::string(strCountry), nID, nCreatorID);
	pGlobalState->AddSpot(pSpot);
	return 0;
}

static int ReadDrillerCallback(void* pGlobalState_, int argc, char** argv, char** azColName)
{
	GlobalState* pGlobalState = (GlobalState*)pGlobalState_;
	// TODO: assert(argc == 5)
	char* strID = argv[0];
	char* strName = argv[1];
	char* strLocation = argv[2];
	char* strDepth = argv[3];
	char* strSpotID = argv[4];
	int nID, nSpotID, nDepth;
	std::stringstream ss;
	ss << strID;
	ss >> nID;
	ss.str("");
	ss.clear();
	ss << strSpotID;
	ss >> nSpotID;
	ss.str("");
	ss.clear();
	ss << strDepth;
	ss >> nDepth;
	ss.str("");
	ss.clear();
	Driller* pDriller = new Driller(std::string(strName), std::string(strLocation), nID, nDepth, nSpotID);
	pGlobalState->AddDriller(pDriller);
	return 0;
}

void GlobalState::InitializeFromDatabase()
{
	// Connect to database
	sqlite3 *db;
	char *strErrMsg = 0;
	int rc = 0;
	rc = sqlite3_open("data.db", &db);
	if(rc)
	{
		std::cerr << "Cannot open database: " << sqlite3_errmsg(db) << std::endl;
		throw new std::exception();
	}

	// Keep database open!
	this->SetDb(db);

	// Read users
	char* strSql = "SELECT * FROM USER;";
	rc = sqlite3_exec(db, strSql, ReadUserCallback, (void*)this, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		std::cerr << "SQL error occurred when querying USER table: " << strErrMsg << std::endl;
		sqlite3_free(strErrMsg);
		throw new std::exception();
	}

	// Read spots
	strSql = "SELECT * FROM SPOT;";
	rc = sqlite3_exec(db, strSql, ReadSpotCallback, (void*)this, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		std::cerr << "SQL error occurred when querying SPOT table: " << strErrMsg << std::endl;
		sqlite3_free(strErrMsg);
		throw new std::exception();
	}

	// Read drillers
	strSql = "SELECT * FROM DRILLER;";
	rc = sqlite3_exec(db, strSql, ReadDrillerCallback, (void*)this, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		std::cerr << "SQL error occurred when querying DRILLER table: " << strErrMsg << std::endl;
		sqlite3_free(strErrMsg);
		throw new std::exception();
	}	
}

std::string GlobalState::GetStatistics()
{
    std::stringstream ss;
	ss << "The best drilling company on this planet, since 1990." << std::endl;
	ss << "We have " << std::dec << this->m_pvecUsers->size() << " customers." << std::endl;
	ss << "We have drilled " << std::dec << this->m_nGlobalDrillingDepth << " miles in total since 1990." << std::endl;
	ss << " ----------------------------------------- !!! Lottery !!! ---------------------------------------------" << std::endl;
	ss << "| To show our gratefulness to your precious support in these years, we will select two customers every |" << std::endl;
	ss << "| three weeks. Please write down your lucky numbers! Winners might be invited to visit the world's     |" << std::endl;
	ss << "| most advanced uranium-enriching company in DPRK.                                                     |" << std::endl;
	ss << "| SEIZE THE OPPORTUNITY!                                                                               |" << std::endl;
	ss << " ------------------------------------------------------------------------------------------------------ " << std::endl;
	ss << "Your lucky numbers are " << /* Small trick here */ std::oct <<  (unsigned int)this->m_pvecUsers << "--" << (unsigned int)this->m_pvecSpots << std::endl;

	return ss.str();
}

bool GlobalState::AddUser(User* pUser)
{
    for(std::vector<User*>::iterator it = this->m_pvecUsers->begin();
        it != this->m_pvecUsers->end();
        ++it)
    {
        User* p = *it;
        if(!strcmp(p->GetName(), pUser->GetName()))
        {
            return false;
        }
    }
	this->m_pvecUsers->push_back(pUser);
    return true;
}

void GlobalState::AddUserToDatabase(User* pUser)
{
	// TODO: assert this->m_pDb != NULL
	std::stringstream ss;
	ss <<"INSERT INTO USER (ID, NAME, PASSWORD, CREATOR, IDENTITY) "
					"VALUES (" << pUser->GetID() << ", '" << pUser->GetName() << "', '" 
					<< pUser->GetPasswordStr() << "', " << pUser->GetCreatorID() << ", "
					<< (pUser->IsAdmin()? 1 : 0) << ");";
	char* strErrMsg;
	int rc = sqlite3_exec(this->m_pDb, ss.str().c_str(), NULL, 0, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		std::cerr << "An error occurred while inserting USER record: " << strErrMsg << std::endl;
		sqlite3_free(strErrMsg);
		throw new std::exception();
	}
}

User* GlobalState::GetUser(char* pName)
{
	for(std::vector<User*>::iterator it = this->m_pvecUsers->begin();
		it != this->m_pvecUsers->end();
		++it)
	{
		User* pUser = *it;
		if(!strcasecmp(pUser->GetName(), pName))
		{
			return pUser;
		}
	}
	return NULL;
}

void GlobalState::AddSpot(Spot* pSpot)
{
	// TODO: Check for duplicated name and throw exception
	this->m_pvecSpots->push_back(pSpot);
}

void GlobalState::AddSpotToDatabase(Spot* pSpot)
{
	// TODO: assert this->m_pDb != NULL
	std::stringstream ss;
	ss <<"INSERT INTO SPOT (ID, CREATORID, NAME, COUNTRY) "
					"VALUES (" << pSpot->GetID() << ", '" << pSpot->GetCreatorID() << "', '" 
					<< pSpot->GetName() << "', '" << pSpot->GetCountry() << "');";
	char* strErrMsg;
	int rc = sqlite3_exec(this->m_pDb, ss.str().c_str(), NULL, 0, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		std::cerr << "An error occurred while inserting SPOT record: " << strErrMsg << std::endl;
		sqlite3_free(strErrMsg);
		throw new std::exception();
	}
}

void GlobalState::AddDriller(Driller* pDriller)
{
	int nSpotID = pDriller->GetSpotID();
	Spot* pSpot = NULL;
	for(std::vector<Spot*>::iterator it = this->m_pvecSpots->begin();
		it != this->m_pvecSpots->end();
		++it)
	{
		Spot* p = *it;
		if(p->GetID() == nSpotID)
		{
			pSpot = p;
			break;
		}
	}
	if(pSpot != NULL)
	{
		pSpot->AddDriller(pDriller);
	}
}

void GlobalState::AddDrillerToDatabase(Driller* pDriller)
{
	// TODO: assert this->m_pDb != NULL
	std::stringstream ss;
	ss <<"INSERT INTO DRILLER (ID, NAME, LOCATION, DEPTH, SPOTID) "
					"VALUES (" << pDriller->GetID() << ", '" << pDriller->GetName() << "', '" 
					<< pDriller->GetLocation() << "', " << pDriller->GetDepth() << ", " << pDriller->GetSpotID() << ");";
	char* strErrMsg;
	int rc = sqlite3_exec(this->m_pDb, ss.str().c_str(), NULL, 0, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		std::cerr << "An error occurred while inserting DRILLER record: " << strErrMsg << std::endl;
		sqlite3_free(strErrMsg);
		throw new std::exception();
	}
}

// If current user is an admin, we should list all users
std::vector<User*> GlobalState::ListUser()
{
	User* pUser = NULL;
	if((pUser = this->GetCurrentUser()) == NULL)
	{
		std::cerr << "[Exception]Current_user == NULL" << std::endl;
		throw new std::exception();
	}
	if(pUser->IsAdmin())
	{
		return *(this->m_pvecUsers);
	}
	else
	{
		std::vector<User*> vec;
		vec.push_back(pUser);
		return vec;
	}
}

// If current user is an admin, we should list all spots
std::vector<Spot*> GlobalState::ListSpot()
{
	User* pUser = NULL;
	if((pUser = this->GetCurrentUser()) == NULL)
	{
		std::cerr << "[Exception]Current_user == NULL" << std::endl;
		throw new std::exception();
	}
	if(pUser->IsAdmin())
	{
		return *(this->m_pvecSpots);
	}
	else
	{
		std::vector<Spot*> vec;
		for(std::vector<Spot*>::iterator it = this->m_pvecSpots->begin();
			it != this->m_pvecSpots->end();
			++it)
		{
			Spot* p = *it;
			if(p->GetCreatorID() == pUser->GetID())
			{
				vec.push_back(p);
			}
		}
		return vec;
	}
}

void GlobalState::AddDepth(int nDelta)
{
	*(unsigned int*)(&this->m_nGlobalDrillingDepth) += nDelta; // Vulnerability here!
}

short GlobalState::GetDepth()
{
	return this->m_nGlobalDrillingDepth;
}

void GlobalState::UpdateUserPasswordInDatabase(User* pUser)
{
	// TODO: assert this->m_pDb != NULL
	std::stringstream ss;
	ss <<"UPDATE USER SET PASSWORD = '" << pUser->GetPasswordStr() << "' WHERE ID = " << pUser->GetID() << ";";
	char* strErrMsg;
	int rc = sqlite3_exec(this->m_pDb, ss.str().c_str(), NULL, 0, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		std::cerr << "An error occurred while updating USER record: " << strErrMsg << std::endl;
		sqlite3_free(strErrMsg);
		throw new std::exception();
	}
}

void GlobalState::UpdateUserIdentityInDatabase(User* pUser)
{
	// TODO: assert this->m_pDb != NULL
	std::stringstream ss;
	if(pUser->IsAdmin())
	{
		ss <<"UPDATE USER SET IDENTITY = 1 WHERE ID = " << pUser->GetID() << ";";	
	}
	else
	{
		ss <<"UPDATE USER SET IDENTITY = 0 WHERE ID = " << pUser->GetID() << ";";
	}
	char* strErrMsg;
	int rc = sqlite3_exec(this->m_pDb, ss.str().c_str(), NULL, 0, &strErrMsg);
	if(rc != SQLITE_OK)
	{
		std::cerr << "An error occurred while updating USER record: " << strErrMsg << std::endl;
		sqlite3_free(strErrMsg);
		throw new std::exception();
	}
}
