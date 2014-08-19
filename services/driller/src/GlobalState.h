#include <string>
#include <vector>
#include <sqlite3.h>

class User;
class Spot;
class Driller;

class GlobalState
{
public:
	GlobalState();
	~GlobalState();
	std::string GetStatistics();
	bool AddUser(User* pUser);
	void AddUserToDatabase(User* pUser);
	void AddSpot(Spot* pSpot);
	void AddSpotToDatabase(Spot* pSpot);
	void AddDriller(Driller* pDriller);
	void AddDrillerToDatabase(Driller* pDriller);
	std::vector<User*> ListUser();
	std::vector<Spot*> ListSpot();
	void RemoveUser();
	void RemoveSpot();
	void RemoveDriller();
	void SetCurrentUser(int nUserID) { m_nCurrentUserID = nUserID; }
	User* GetCurrentUser();
	int GetCurrentUserID() { return m_nCurrentUserID; }
	User* GetUser(char* pName);
	void SetMaxUserID(int nMaxID);
	int GetMaxUserID();
	void SetMaxSpotID(int nMaxID);
	int GetMaxSpotID();
	void SetMaxDrillerID(int nMaxID);
	int GetMaxDrillerID();
	int IncrementMaxUserID() { ++m_nMaxUserID; }
	void SetDb(sqlite3 *pDb) { m_pDb = pDb; }
	sqlite3* GetDb() { return m_pDb; }
	void AddDepth(int nDelta);
	short GetDepth();
	void UpdateUserPasswordInDatabase(User* pUser);
	void UpdateUserIdentityInDatabase(User* pUser);
private:
	void InitializeFromDatabase();
private:	
	short m_nDrillersCount;
	short m_nGlobalDrillingDepth; /* Vulnerability: It's short, but it's treated as an int */
	std::vector<User*>* m_pvecUsers;
	std::vector<Spot*>* m_pvecSpots;
	int m_nCurrentUserID; /* We keep the ID of the current user. */
	int m_nMaxUserID;
	int m_nMaxSpotID;
	int m_nMaxDrillerID;
	unsigned int m_nLotteryNumber1;
	unsigned int m_nLotteryNumber2;
	sqlite3 *m_pDb;
};
