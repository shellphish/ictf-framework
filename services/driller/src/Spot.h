#include <string>
#include <vector>

class Driller;

class Spot
{
public:
	Spot(const std::string &strName, const std::string &strCountry, int nId, int nCreatorID);
	Spot(const std::string &strName, const std::string &strCountry, int nCreatorID);
	void AddDriller(Driller* pDriller);
    std::vector<Driller*> GetAllDrillers();
    int GetDrillersCount();
    int GetID() { return m_nID; }
    int GetCreatorID() { return m_nCreatorID; }
    char* GetName() { return m_strSpotName; }
    char* GetCountry() { return m_strCountry; }
private:
	int m_nCreatorID; /* 4 bytes. Why we must put creator id in front of id? :D */
	int m_nID; /* 4 bytes */
	char m_strCountry[40];
	char m_strSpotName[40];
	std::vector<Driller*> m_vecDrillers;
};
