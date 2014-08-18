#include <string.h>
#include "Spot.h"
#include "GlobalState.h"

extern GlobalState* g_pGlobalState;

Spot::Spot(const std::string &strName, const std::string &strCountry, int nID, int nCreatorID)
{
    this->m_nID = nID;
    this->m_nCreatorID = nCreatorID;

    std::string strNameTrimmed = strName.substr(0, sizeof(this->m_strSpotName) - 1);
    strcpy(this->m_strSpotName, strNameTrimmed.c_str());

    std::string strCountryTrimmed = strCountry.substr(0, sizeof(this->m_strCountry) - 1);
    strcpy(this->m_strCountry, strCountryTrimmed.c_str());
}

Spot::Spot(const std::string &strName, const std::string &strCountry, int nCreatorID)
{
	this->m_nID = g_pGlobalState->GetMaxSpotID() + 1;
    this->m_nCreatorID = nCreatorID;

    std::string strNameTrimmed = strName.substr(0, sizeof(this->m_strSpotName) - 1);
    strcpy(this->m_strSpotName, strNameTrimmed.c_str());

    std::string strCountryTrimmed = strCountry.substr(0, sizeof(this->m_strCountry) - 1);
    strcpy(this->m_strCountry, strCountryTrimmed.c_str());
}

void Spot::AddDriller(Driller* pDriller)
{
    this->m_vecDrillers.push_back(pDriller);
}

std::vector<Driller*> Spot::GetAllDrillers()
{
    return this->m_vecDrillers;
}

int Spot::GetDrillersCount()
{
	return this->m_vecDrillers.size();
}