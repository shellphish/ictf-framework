class MenuEntry
{
public:
	MenuEntry(const std::string& strCaption, int (*pHandler)(MenuEntry* pEntry, int nFd));
	void PrintPrompt(int nFd);
	int Handler(int nFd);
	std::string GetCaption();
	void AddEntry(MenuEntry* pMenuEntry);
	MenuEntry* GetEntry(int nID);
private:
	std::string m_strCaption;
	std::vector<MenuEntry*> m_vecEntries;
	int (*m_pHandler)(MenuEntry* pEntry, int nFd);
};

#define MENU_EXIT -1