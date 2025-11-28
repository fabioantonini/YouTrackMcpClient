import os
import json
import requests
from dotenv import load_dotenv

# Carica variabili d'ambiente dal file .env, se presente
load_dotenv()

# Recupera le configurazioni necessarie dalle variabili d'ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YT_BASE_URL = os.getenv("YT_BASE_URL", "").rstrip("/")  # rimuove eventuale slash finale
YT_TOKEN = os.getenv("YT_TOKEN")

# Controllo di base sulle configurazioni
# -> l'API key è obbligatoria da env
if not OPENAI_API_KEY:
    raise RuntimeError("Configurazione mancante! Assicurarsi che OPENAI_API_KEY sia impostata.")

class GPTParser:
    """Utilizza l'API OpenAI per interpretare comandi in linguaggio naturale e produrre un JSON strutturato."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Endpoint ChatGPT API
        self.api_url = "https://api.openai.com/v1/chat/completions"
        # Prompt di sistema che istruisce GPT sul formato di output
        self.system_prompt = (
            "Sei un assistente che converte un comando in linguaggio naturale in un'azione JSON per YouTrack. "
            "Rispondi SOLO con un JSON contenente 'action' e i parametri necessari, senza spiegazioni. "
            "Per delete_issue DEVI SEMPRE includere la chiave 'issue' con l'ID leggibile dell'issue (es. 'SUP-3'). "
            "Azioni possibili: create_project, create_issue, update_issue, change_issue_assignee, "
            "delete_issue, list_issues, summarize_project, create_epic, create_epic_with_children, link_issues, show_epic_hierarchy. "
            "Per list_issues usa sempre un oggetto 'filters' con i filtri della query, ad esempio:\n"
            '{"action": "list_issues", "filters": {"project": "SUP", "Assignee": "admin"}}\n'
            "I nomi delle chiavi dentro 'filters' devono essere i nomi di campo usati nel linguaggio di ricerca di YouTrack "
            "(es. project, Assignee, Priority, State, Type, ecc.)."
            "Per update_issue usa un campo 'issue' con l'ID leggibile (es. 'SUP-3') e un oggetto 'fields' con i campi da aggiornare, ad esempio:\n"
            '{"action": "update_issue", "issue": "SUP-3", "fields": {"summary": "Nuovo titolo", "Priority": "Major", "assignee": "admin"}}\n'
            "Per casi avanzati puoi anche aggiungere 'customFields' come array YouTrack-ready:"
            '{"action": "update_issue", "issue": "SUP-3", "customFields": [{"name": "MyField", "value": {"name": "Foo"}}]}'
            "Per summarize_project DEVI SEMPRE includere la chiave 'project' con la chiave del progetto (es. 'SUP'), ad esempio:\n"
            '{"action": "summarize_project", "project": "SUP"}'
            "Per create_issue DEVI SEMPRE usare le chiavi top-level: "
            "'project', 'summary', 'description', 'priority', 'assignee'. "
            "Non inserire MAI questi campi dentro 'fields'. "
            "Esempio corretto:\n"
            '{"action": "create_issue", "project": "SUP", "summary": "Titolo", "description": "Testo", "priority": "Normal"}\n'
            "Esempio NON valido (da evitare):\n"
            '{"action": "create_issue", "fields": {"project": "SUP", "summary": "Titolo"}}\n'
            "Per create_epic usa lo stesso formato di create_issue, ma con action='create_epic', ad esempio:\n"
            '{"action": "create_epic", "project": "SUP", "summary": "Nuova funzionalità", "description": "Descrizione", "priority": "Major", "assignee": "admin"}\n'
            "Per create_epic_with_children usa:\n"
            '{"action": "create_epic_with_children", "project": "SUP", "epic": {"summary": "Nuovo modulo WiFi", "priority": "Major"}, '
            '"children": [ {"summary": "Aggiornare driver", "priority": "Normal"}, {"summary": "Test di stabilità", "priority": "Major"} ] }\n'
            "Per link_issues DEVI SEMPRE fornire 'from', 'to' e 'link_type', ad esempio:\n"
            '{"action": "link_issues", "from": "SUP-10", "to": "SUP-11", "link_type": "subtask"}\n'
        )

    def parse_command(self, user_command: str) -> dict:
        """Invia il comando utente a GPT-4 e ritorna il JSON interpretato come dizionario Python."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Costruisce il payload per l'API OpenAI
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_command}
            ],
            # Chiediamo la massima aderenza al formato JSON
            "temperature": 0,  # deterministico
            "max_tokens": 200,
            "n": 1,
            "stop": None
        }
        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()  # in caso di errore HTTP, genera eccezione
        result = response.json()
        # Estrae il contenuto della risposta (messaggio dell'assistente)
        assistant_message = result["choices"][0]["message"]["content"]
        # Converte la stringa JSON in un dizionario Python
        action_data = json.loads(assistant_message)
        return action_data

    def summarize_issues(self, project_key: str, issues: list) -> str:
        """
        Usa GPT per riassumere lo stato di un progetto a partire dalla lista di issue.
        'issues' è una lista di dict con almeno id, summary, project.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Prepariamo un prompt compatto con la lista issue in JSON
        issues_text = json.dumps(issues, ensure_ascii=False, indent=2)

        system_msg = (
            "Sei un assistente che riassume lo stato di un progetto YouTrack per un essere umano. "
            "Hai a disposizione una lista di issue (con id e summary, eventualmente altri campi). "
            "Devi fornire un riassunto discorsivo e sintetico in italiano: cosa sembra essere in lavorazione, "
            "quali sono i problemi principali, eventuali punti di attenzione. "
            "Non ripetere tutto l'elenco in modo pedissequo, ma estrai le informazioni rilevanti."
        )

        user_msg = (
            f"Progetto: {project_key}\n"
            f"Lista issue (JSON):\n{issues_text}"
        )

        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "temperature": 0.3,
            "max_tokens": 600
        }

        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

class YouTrackClient:
    """Client per eseguire operazioni su YouTrack tramite API REST e MCP."""
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        # Header di autenticazione e tipo di contenuto JSON
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        # Cache per ID progetti e utenti (per evitare lookup ripetuti)
        self.project_cache = {}
        self.user_cache = {}
    
    def _get_current_user_id(self):
        """Recupera l'ID dell'utente corrente (associato al token) tramite API YouTrack."""
        url = f"{self.base_url}/api/users/me?fields=id"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("id")
    
    def _find_user_by_name_or_login(self, name_or_login: str):
        """Trova un utente su YouTrack dato login o nome.
        Prova prima l'endpoint diretto /api/users/{login}, poi la search API.
        Restituisce dict {id, login} oppure None.
        """
        if name_or_login in self.user_cache:
            return self.user_cache[name_or_login]

        # 1) Tentativo diretto: /api/users/{login}
        url_direct = f"{self.base_url}/api/users/{name_or_login}?fields=id,login,fullName"
        resp = requests.get(url_direct, headers=self.headers)
        print(f"[DEBUG] GET {url_direct} -> {resp.status_code}")
        if resp.status_code == 200:
            u = resp.json()
            user = {"id": u["id"], "login": u["login"]}
            self.user_cache[name_or_login] = user
            print(f"[DEBUG] Utente '{name_or_login}' trovato via endpoint diretto: {user}")
            return user

        # 2) Fallback: search per login
        url_search_login = f"{self.base_url}/api/users?fields=id,login,fullName&query=login:{name_or_login}"
        resp = requests.get(url_search_login, headers=self.headers)
        print(f"[DEBUG] GET {url_search_login} -> {resp.status_code}")
        if resp.ok:
            users = resp.json()
            print(f"[DEBUG] Risultati search login: {users}")
            if users:
                u = users[0]
                user = {"id": u["id"], "login": u["login"]}
                self.user_cache[name_or_login] = user
                return user

        # 3) Fallback: search per nome (fullName)
        url_search_name = f"{self.base_url}/api/users?fields=id,login,fullName&query=name:{name_or_login}"
        resp = requests.get(url_search_name, headers=self.headers)
        print(f"[DEBUG] GET {url_search_name} -> {resp.status_code}")
        if resp.ok:
            users = resp.json()
            print(f"[DEBUG] Risultati search name: {users}")
            if users:
                u = users[0]
                user = {"id": u["id"], "login": u["login"]}
                self.user_cache[name_or_login] = user
                return user

        print(f"[WARN] Nessun utente trovato per '{name_or_login}'")
        return None

    
    def _get_project_id(self, project_key: str):
        """Restituisce l'ID interno di un progetto dato il suo shortName (chiave)."""
        if project_key in self.project_cache:
            return self.project_cache[project_key]

        # 1) Prova endpoint diretto /api/admin/projects/{project_key}
        url_direct = f"{self.base_url}/api/admin/projects/{project_key}?fields=id,shortName"
        resp = requests.get(url_direct, headers=self.headers)
        print(f"[DEBUG] GET {url_direct} -> {resp.status_code}")
        if resp.status_code == 200:
            proj = resp.json()
            proj_id = proj["id"]
            self.project_cache[project_key] = proj_id
            print(f"[DEBUG] Project '{project_key}' has internal id '{proj_id}' (via direct endpoint)")
            return proj_id

        # 2) Fallback: usa la search API
        url_search = f"{self.base_url}/api/admin/projects?fields=id,shortName&query=shortName:{project_key}"
        resp = requests.get(url_search, headers=self.headers)
        print(f"[DEBUG] GET {url_search} -> {resp.status_code}")
        resp.raise_for_status()
        projects = resp.json()
        print(f"[DEBUG] Projects search result: {projects}")
        if projects:
            proj_id = projects[0]["id"]
            self.project_cache[project_key] = proj_id
            print(f"[DEBUG] Project '{project_key}' has internal id '{proj_id}' (via search)")
            return proj_id

        # Se arriviamo qui, non abbiamo trovato il progetto
        raise ValueError(f"Project '{project_key}' not found on YouTrack")

    
    def create_project(self, name: str, key: str, description: str = ""):
        """Crea un nuovo progetto con nome e key specificati. Restituisce l'ID leggibile (shortName) del progetto creato."""
        # Prepara il corpo JSON con i campi richiesti per la creazione progetto
        # Campi obbligatori: name, shortName, leader (id utente leader):contentReference[oaicite:18]{index=18}.
        current_user_id = self._get_current_user_id()
        project_data = {
            "name": name,
            "shortName": key,
            "leader": { "id": current_user_id }
        }
        if description:
            project_data["description"] = description
        url = f"{self.base_url}/api/admin/projects?fields=id,shortName,name,leader(login)"
        resp = requests.post(url, headers=self.headers, json=project_data)
        resp.raise_for_status()
        proj = resp.json()
        proj_key = proj.get("shortName", key)
        print(f"✅ Progetto '{proj.get('name')}' creato con chiave {proj_key}")
        return proj_key
    
    def create_issue(self, project: str, summary: str, description: str = "", assignee: str = "", priority: str = ""):
        """Crea un nuovo issue nel progetto specificato. Restituisce l'ID leggibile dell'issue creato."""
        # Ottiene l'ID interno del progetto (ora, se non esiste, solleva errore chiaro)
        project_id = self._get_project_id(project)

        issue_data = {
            "summary": summary,
            "project": { "id": project_id }
        }
        if description:
            issue_data["description"] = description

        # Prepara la lista dei customFields se necessari
        custom_fields = []
        if assignee:
            user = self._find_user_by_name_or_login(assignee)
            print(f"[DEBUG] Risultato lookup utente '{assignee}': {user}")
            if user:
                custom_fields.append({
                    "name": "Assignee",
                    "$type": "SingleUserIssueCustomField",
                    "value": { "login": user["login"] }
                })
            else:
                print(f"[WARN] Utente '{assignee}' non trovato, issue creato senza assignee.")

        if priority:
            # Imposta il campo di Priorità con il nome fornito:contentReference[oaicite:20]{index=20}
            custom_fields.append({
                "name": "Priority",
                "$type": "SingleEnumIssueCustomField",
                "value": { "name": priority }
            })
        if custom_fields:
            issue_data["customFields"] = custom_fields
        # Chiamata API per creare l'issue
        url = f"{self.base_url}/api/issues?fields=id,idReadable"
        # DEBUG: stampiamo il payload che stiamo inviando
        print("[DEBUG] Issue payload che sto per inviare a YouTrack:")
        print(json.dumps(issue_data, indent=2, ensure_ascii=False))
        resp = requests.post(url, headers=self.headers, json=issue_data)
        resp.raise_for_status()
        issue = resp.json()
        issue_id_readable = issue.get("idReadable")
        print(f"✅ Issue creato con ID {issue_id_readable}")
        return issue_id_readable
    
    def update_issue(self, issue_id: str, fields: dict | None = None, custom_fields: list | None = None):
        """
        Aggiorna uno o più campi di un issue in modo generico.

        - fields: dizionario {nomeCampo: valore}, es:
            {
              "summary": "Nuovo titolo",
              "description": "Testo aggiornato",
              "assignee": "admin",
              "Priority": "Major",
              "State": "Submitted"
            }

          Regole:
          - summary, description -> campi top-level dell'issue.
          - 'assignee' (case-insensitive) -> custom field 'Assignee' con value {login: ...}.
          - 'priority' (minuscolo) -> custom field 'Priority' con value {name: ...}.
          - 'Priority', 'State', 'Type' (case-sensitive) -> trattati come enum: value {name: valore}.
          - per tutti gli altri campi:
              - se value è un dict -> usato come value così com'è
              - altrimenti -> usato come value scalare (stringa, numero, ecc.)

        - custom_fields: lista di entry customFields già pronte, es:
            [
              { "name": "MyCustomEnum", "value": { "name": "Foo" } }
            ]
          che vengono aggiunte senza modifiche.
        """
        update_data: dict = {}
        cf_list: list = []

        fields = fields or {}
        custom_fields = custom_fields or []

        # Campi top-level
        if "summary" in fields:
            update_data["summary"] = fields.pop("summary")
        if "description" in fields:
            update_data["description"] = fields.pop("description")

        # Altri campi
        for field_name, value in fields.items():
            lname = field_name.lower()

            if lname == "assignee":
                user = self._find_user_by_name_or_login(value)
                if not user:
                    print(f"[WARN] Utente '{value}' non trovato, campo Assignee ignorato.")
                    continue
                cf_list.append({
                    "name": "Assignee",
                    "$type": "SingleUserIssueCustomField",
                    "value": { "login": user["login"] }
                })

            elif lname == "priority":
                # sintassi compatibile con enum standard
                cf_list.append({
                    "name": "Priority",
                    "$type": "SingleEnumIssueCustomField",
                    "value": { "name": value }
                })

            elif field_name in ("Priority", "State", "Type"):
                # altri enum tipici: usiamo {name: valore}
                cf_list.append({
                    "name": field_name,
                    "$type": "SingleEnumIssueCustomField",
                    "value": { "name": value }
                })

            else:
                # caso generico:
                # - se value è un dict, lo usiamo direttamente come value
                # - se è scalare (stringa/numero), lo usiamo come value scalare
                if isinstance(value, dict):
                    cf_list.append({
                        "name": field_name,
                        "$type": "SimpleIssueCustomField",
                        "value": value
                    })
                else:
                    cf_list.append({
                        "name": field_name,
                        "value": value
                    })

        # Aggiungi eventuali customFields raw passati da fuori
        cf_list.extend(custom_fields)

        if cf_list:
            update_data["customFields"] = cf_list

        if not update_data:
            print("[WARN] Nessun campo da aggiornare.")
            return None

        print("[DEBUG] Payload update_issue che sto per inviare:")
        print(json.dumps(update_data, indent=2, ensure_ascii=False))

        url = f"{self.base_url}/api/issues/{issue_id}?fields=id,idReadable"
        resp = requests.post(url, headers=self.headers, json=update_data)
        if not resp.ok:
            print("[DEBUG] YouTrack ha risposto con errore in update_issue:")
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
            resp.raise_for_status()

        updated = resp.json()
        issue_key = updated.get("idReadable", issue_id)
        print(f"✅ Issue {issue_key} aggiornato.")
        return issue_key
    
    def change_issue_assignee(self, issue_id: str, assignee: str):
        """Modifica l'assegnatario di un issue esistente."""
        return self.update_issue(issue_id, {"assignee": assignee})
    
    def delete_issue(self, issue_id: str):
        """Elimina l'issue specificato (usa l'ID leggibile o quello interno)."""
        url = f"{self.base_url}/api/issues/{issue_id}"
        resp = requests.delete(url, headers=self.headers)
        if resp.status_code == 404:
            print(f"⚠️ Issue {issue_id} non trovato o già eliminato.")
            return False
        resp.raise_for_status()
        print(f"✅ Issue {issue_id} eliminato con successo.")
        return True

    def list_issues(self, filters: dict | None = None, limit: int = 20):
        """
        Restituisce la lista degli issue.
        'filters' è un dizionario generico {campo: valore} che viene tradotto
        direttamente nel linguaggio di query di YouTrack.
        """
        base_url = f"{self.base_url}/api/issues"
        params = {
            "fields": "id,idReadable,summary,project(shortName),customFields(name,value(name,login))",
            "$top": limit,
        }

        # 👇 Alias "furbi" per i nomi campo usati spesso in linguaggio naturale o da GPT
        alias_map = {
            # se GPT (o noi) scriviamo "Parent for": X intendendo
            # "dammi i subtask di X", lo mappiamo a "Subtask of"
            "Parent for": "Subtask of",
            "parent for": "Subtask of",
            # altri alias comodi
            "subtasks": "Subtask of",
            "subtask": "Subtask of",
        }

        query_parts = []
        if filters:
            for field, value in filters.items():
                # normalizza il campo se esiste un alias
                norm_field = alias_map.get(field, field)
                query_parts.append(f"{norm_field}: {value}")
        if query_parts:
            params["query"] = " ".join(query_parts)

        print(f"[DEBUG] GET {base_url} params={params}")
        resp = requests.get(base_url, headers=self.headers, params=params)
        if not resp.ok:
            print("[DEBUG] YouTrack ha risposto con errore in list_issues:")
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
            resp.raise_for_status()

        issues = resp.json()

        results = []
        for issue in issues:
            issue_key = issue.get("idReadable")
            summary = issue.get("summary")
            project_short = issue.get("project", {}).get("shortName")
            results.append({
                "id": issue_key,
                "summary": summary,
                "project": project_short,
            })

        return results

    def _get_issue_db_id(self, issue_id_readable: str) -> str:
        """Restituisce l'ID di database di un issue dato l'ID leggibile (es. SUP-3)."""
        url = f"{self.base_url}/api/issues/{issue_id_readable}?fields=id"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        return data["id"]

    def _get_link_type_id(self, link_name: str) -> str | None:
        """
        Trova l'ID del tipo di link a partire da un nome 'umano':
        - prova a confrontare con name, sourceToTarget, targetToSource, localized*
        - gestisce un paio di sinonimi per Subtask.
        """
        if not hasattr(self, "_link_type_cache"):
            self._link_type_cache = {}

        key = link_name.strip().lower()
        if key in self._link_type_cache:
            return self._link_type_cache[key]

        # normalizzazione minima per i subtasks
        if key in ("subtask", "subtask of", "parent for", "epic-child"):
            normalized = "subtask"
        else:
            normalized = key

        url = f"{self.base_url}/api/issueLinkTypes"
        params = {
            "fields": "id,name,sourceToTarget,targetToSource,localizedSourceToTarget,localizedTargetToSource"
        }
        resp = requests.get(url, headers=self.headers, params=params)
        if not resp.ok:
            print(f"[DEBUG] Errore nella lettura dei link types: {resp.status_code} {resp.text}")
            resp.raise_for_status()
        types = resp.json()

        found_id = None
        for t in types:
            candidates = [
                t.get("name"),
                t.get("sourceToTarget"),
                t.get("targetToSource"),
                t.get("localizedSourceToTarget"),
                t.get("localizedTargetToSource"),
            ]
            candidates = [c.lower() for c in candidates if c]
            if normalized in candidates:
                found_id = t["id"]
                break

            # fallback per 'subtask' → tipo 'Subtask'
            if normalized == "subtask" and t.get("name", "").lower() == "subtask":
                found_id = t["id"]
                break

        if not found_id:
            print(f"[WARN] Tipo di link '{link_name}' non trovato. Nessun link creato.")
            return None

        self._link_type_cache[key] = found_id
        return found_id

    def link_issues(self, from_issue: str, to_issue: str, link_type_name: str = "relates") -> bool:
        """
        Crea un link tra due issue.
        - from_issue: ID leggibile dell'issue sorgente (es. SUP-10)
        - to_issue:   ID leggibile dell'issue target (es. SUP-8)
        - link_type_name: nome del link (es. 'relates', 'depends on', 'subtask', 'parent for')
        """
        link_type_id = self._get_link_type_id(link_type_name)
        if not link_type_id:
            return False

        # YouTrack vuole l'ID DB dell'issue target
        target_db_id = self._get_issue_db_id(to_issue)

        url = f"{self.base_url}/api/issues/{from_issue}/links/{link_type_id}/issues"
        payload = { "id": target_db_id }

        print(f"[DEBUG] POST {url} body={payload}")
        resp = requests.post(url, headers=self.headers, json=payload)
        if not resp.ok:
            print("[DEBUG] Errore nella creazione del link:")
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
            resp.raise_for_status()

        print(f"✅ Link '{link_type_name}' creato tra {from_issue} -> {to_issue}")
        return True

    def create_epic(self, project: str, summary: str,
                    description: str = "", assignee: str = "", priority: str = "") -> str:
        """
        Crea un issue e lo imposta come Epic (Type = Epic).
        Restituisce l'ID leggibile dell'Epic (es. SUP-10).
        """
        epic_id = self.create_issue(project, summary, description, assignee, priority)
        # Imposta Type = Epic
        self.update_issue(epic_id, fields={"Type": "Epic"})
        return epic_id

    def create_epic_with_children(self, project: str,
                                  epic_fields: dict,
                                  children: list[dict],
                                  child_link_type: str = "subtask") -> dict:
        """
        Crea un Epic e una serie di task figli, collegandoli come subtasks (o altro link type).
        epic_fields: dict con almeno 'summary', opzionali description/assignee/priority.
        children: lista di dict, ognuno con almeno 'summary', opzionali description/assignee/priority.
        Ritorna un dict con gli ID:
           { "epic": "SUP-10", "children": ["SUP-11", "SUP-12", ...] }
        """
        epic_summary = epic_fields.get("summary") or epic_fields.get("title")
        if not epic_summary:
            raise ValueError("Per create_epic_with_children è necessario almeno epic.summary")

        epic_desc = epic_fields.get("description", "")
        epic_assignee = epic_fields.get("assignee", "")
        epic_priority = epic_fields.get("priority", "")

        epic_id = self.create_epic(project, epic_summary, epic_desc, epic_assignee, epic_priority)

        child_ids: list[str] = []
        for child in children:
            c_summary = child.get("summary") or child.get("title")
            if not c_summary:
                print("[WARN] Child senza summary, saltato.")
                continue
            c_desc = child.get("description", "")
            c_assignee = child.get("assignee", "")
            c_priority = child.get("priority", "")

            child_id = self.create_issue(project, c_summary, c_desc, c_assignee, c_priority)
            child_ids.append(child_id)

            # Link epic -> child come subtask (o altro tipo)
            self.link_issues(child_id, epic_id, child_link_type)

        print(f"✅ Epic {epic_id} creato con figli {child_ids}")
        return {"epic": epic_id, "children": child_ids}

    def get_children_of_epic(self, epic_id: str):
        """
        Restituisce tutti i subtasks dell'Epic in formato leggibile.
        """
        url = f"{self.base_url}/api/issues"
        params = {
            # ci bastano id, summary, Type e Priority
            "fields": "id,idReadable,summary,customFields(name,value(name))",
            # cerchiamo TUTTI gli issue che sono 'subtask of' l'Epic
            "query": f"subtask of: {epic_id}"
        }
        print(f"[DEBUG] GET {url} params={params}")
        resp = requests.get(url, headers=self.headers, params=params)
        if not resp.ok:
            print(f"[DEBUG] Errore nella ricerca subtasks: {resp.status_code} {resp.text}")
            resp.raise_for_status()

        issues = []
        for item in resp.json():
            summary = item.get("summary", "")
            id_readable = item.get("idReadable", "")
            custom_fields = item.get("customFields", [])
            cf = {}
            for f in custom_fields:
                name = f.get("name")
                val = f.get("value")
                if isinstance(val, dict):
                    cf[name] = val.get("name")
            issues.append({
                "id": id_readable,
                "summary": summary,
                "type": cf.get("Type"),
                "priority": cf.get("Priority")
            })

        return issues

# Esecuzione principale: loop per leggere comandi da console
if __name__ == "__main__":
    import argparse

    arg_parser = argparse.ArgumentParser(
        description="Interfaccia YouTrack via linguaggio naturale (GPT + REST API)."
    )
    arg_parser.add_argument(
        "--yt-url",
        dest="yt_url",
        help="Base URL di YouTrack (es. https://foo.youtrack.cloud)"
    )
    arg_parser.add_argument(
        "--yt-token",
        dest="yt_token",
        help="Token permanente di YouTrack"
    )
    args = arg_parser.parse_args()

    base_url = (args.yt_url or YT_BASE_URL or "").rstrip("/")
    token = args.yt_token or YT_TOKEN

    if not base_url or not token:
        raise RuntimeError(
            "YouTrack non configurato: specificare YT_BASE_URL e YT_TOKEN come variabili "
            "d'ambiente oppure usare --yt-url e --yt-token da riga di comando."
        )

    parser = GPTParser(OPENAI_API_KEY)
    yt = YouTrackClient(base_url, token)

    print("💡 Applicazione YouTrack Natural Language pronta. Inserisci un comando (o 'exit' per uscire).")
    while True:
        try:
            user_input = input("> ")
        except (EOFError, KeyboardInterrupt):
            break  # esce in caso di Ctrl+C o fine input
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "esci"):
            print("👋 Uscita dall'applicazione.")
            break
        try:
            # Passa il comando a GPT-4 per l'interpretazione
            action_data = parser.parse_command(user_input)
            print("[DEBUG] JSON interpretato da GPT:")
            print(json.dumps(action_data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Errore nell'interpretazione del comando: {e}")
            continue

        # Esegue l'azione appropriata in base al JSON ricevuto
        action = action_data.get("action")
        try:
            if action == "create_project":
                name = action_data.get("name") or action_data.get("project_name")
                key = action_data.get("key") or action_data.get("project_key")
                description = action_data.get("description", "")
                if not name or not key:
                    print("⚠️ Il comando non specifica nome e chiave del progetto.")
                else:
                    yt.create_project(name, key, description)

            elif action == "create_issue":
                fields = action_data.get("fields") or {}
                # project può stare top-level oppure dentro fields
                project = (
                    action_data.get("project")
                    or action_data.get("project_key")
                    or fields.get("project")
                )
                summary = (
                    action_data.get("summary")
                    or fields.get("summary")
                    or action_data.get("title")
                    or "Nuovo Issue"
                )
                description = (
                    action_data.get("description")
                    or fields.get("description")
                    or ""
                )
                assignee = (
                    action_data.get("assignee")
                    or fields.get("assignee")
                    or ""
                )
                priority = (
                    action_data.get("priority")
                    or fields.get("Priority")  # GPT spesso usa 'Priority' maiuscolo
                    or fields.get("priority")
                    or ""
                )
                if not project:
                    print("⚠️ Il comando non specifica il progetto per create_issue.")
                else:
                    yt.create_issue(project, summary, description, assignee, priority)

            elif action == "create_epic":
                fields = action_data.get("fields") or {}
                project = (
                    action_data.get("project")
                    or action_data.get("project_key")
                    or fields.get("project")
                )
                summary = (
                    action_data.get("summary")
                    or fields.get("summary")
                    or action_data.get("title")
                )
                description = (
                    action_data.get("description")
                    or fields.get("description")
                    or ""
                )
                assignee = (
                    action_data.get("assignee")
                    or fields.get("assignee")
                    or ""
                )
                priority = (
                    action_data.get("priority")
                    or fields.get("Priority")
                    or fields.get("priority")
                    or ""
                )
                if not project or not summary:
                    print("⚠️ Per create_epic servono almeno project e summary.")
                else:
                    yt.create_epic(project, summary, description, assignee, priority)

            elif action == "create_epic_with_children":
                project = action_data.get("project") or action_data.get("project_key")
                epic = action_data.get("epic") or {}
                children = action_data.get("children") or []
                link_type = action_data.get("link_type") or "subtask"

                if not project:
                    print("⚠️ Per create_epic_with_children serve il project.")
                elif not epic:
                    print("⚠️ Per create_epic_with_children serve l'oggetto 'epic'.")
                else:
                    yt.create_epic_with_children(project, epic, children, child_link_type=link_type)

            elif action == "update_issue":
                issue = action_data.get("issue") or action_data.get("issue_id")
                fields = action_data.get("fields") or {}
                custom_fields = action_data.get("customFields") or []

                if not issue:
                    print("⚠️ Il comando non specifica l'issue da aggiornare.")
                elif not fields and not custom_fields:
                    print("⚠️ Nessun campo da aggiornare per update_issue.")
                else:
                    yt.update_issue(issue, fields=fields, custom_fields=custom_fields)

            elif action == "change_issue_assignee":
                issue = action_data.get("issue") or action_data.get("issue_id")
                assignee = action_data.get("assignee") or action_data.get("new_assignee")
                if not issue or not assignee:
                    print("⚠️ Specificare sia l'issue che il nuovo assegnatario.")
                else:
                    yt.change_issue_assignee(issue, assignee)

            elif action == "delete_issue":
                issue = action_data.get("issue") or action_data.get("issue_id")
                if not issue:
                    print("⚠️ Specificare l'ID dell'issue da eliminare.")
                else:
                    yt.delete_issue(issue)

            elif action == "list_issues":
                filters = action_data.get("filters") or {}
                limit = action_data.get("limit", 20)
                issues = yt.list_issues(filters=filters, limit=limit)
                print("📋 Lista issue:")
                if not issues:
                    print("   (nessun issue trovato)")
                for i in issues:
                    print(f" - {i['id']} [{i['project']}] {i['summary']}")

            elif action == "summarize_project":
                project = action_data.get("project")
                if not project:
                    print("⚠️ Il comando non specifica il progetto da riassumere.")
                else:
                    filters = {"project": project}
                    issues = yt.list_issues(filters=filters, limit=50)
                    if not issues:
                        print(f"📋 Nessun issue trovato per il progetto {project}.")
                    else:
                        summary = parser.summarize_issues(project, issues)
                        print("📊 Riassunto stato progetto", project)
                        print(summary)

            elif action == "link_issues":
                from_issue = action_data.get("from")
                to_issue = action_data.get("to")
                link_type = action_data.get("link_type") or "relates"
                if not from_issue or not to_issue:
                    print("⚠️ Per link_issues servono 'from' e 'to'.")
                else:
                    yt.link_issues(from_issue, to_issue, link_type)
            elif action == "show_epic_hierarchy":
                epic_id = (
                    action_data.get("epic")
                    or action_data.get("issue")
                    or action_data.get("issue_id")
                )
                if not epic_id:
                    print("⚠️ Devi specificare l'Epic, es: SUP-17")
                else:
                    children = yt.get_children_of_epic(epic_id)

                    print(f"\n📂 Gerarchia per Epic {epic_id}\n")
                    print(f"{epic_id}")

                    if not children:
                        print("   (Nessun subtask presente)")
                    else:
                        for c in children:
                            print(f"   └── {c['id']} {c['summary']} ({c['type']} – {c['priority']})")
                    print("")

            else:
                print(f"⚠️ Azione non riconosciuta o non supportata: {action}")

        except Exception as e:
            print(f"❌ Errore durante l'esecuzione dell'azione: {e}")
