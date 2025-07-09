# Configuration for Hackathon Project Provisioning CLI

# List of admin emails who will be Project Owners
ADMIN_EMAILS = [
    'edwardc@pingda.altostrat.com',
    'admin@pingda.altostrat.com'
]

# Your Google Cloud Billing Account ID (e.g., 'billingAccounts/012345-6789AB-CDEF01')
BILLING_ACCOUNT_ID = 'billingAccounts/018E37-168CF2-4084EE'

# Default budget amount for playground projects (per month in USD)
PLAYGROUND_PROJECT_BUDGET_USD = 5

# Default budget amount for team projects (per month in USD)
TEAM_PROJECT_BUDGET_USD = 100

# List of Google APIs to enable for new projects
APIS_TO_ENABLE = [
    'aiplatform.googleapis.com',
    'storage.googleapis.com',
    'bigquery.googleapis.com',
    'cloudfunctions.googleapis.com',
    'run.googleapis.com',
    'logging.googleapis.com',
    'monitoring.googleapis.com',
    'iam.googleapis.com',
    'cloudresourcemanager.googleapis.com',
    'serviceusage.googleapis.com',
    'cloudbilling.googleapis.com',
]

# Folder names
MAIN_FOLDER_NAME = "Hackathon Playground"
GENERAL_FOLDER_NAME = "Individual Attendees"
TEAM1_FOLDER_NAME = "Hackathon Batch1"
TEAM2_FOLDER_NAME = "Hackathon Batch2"

# Project Id/Naming Conventions
PLAYGROUND_PROJECT_ID_PREFIX = "idv-"
PLAYGROUND_PROJECT_ID_SUFFIX = ""
PLAYGROUND_PROJECT_NAME_PREFIX = "idv attendee "
PLAYGROUND_PROJECT_NAME_SUFFIX = ""

TEAM_PROJECT_ID_PREFIX = "team-"
TEAM_PROJECT_ID_SUFFIX = ""
TEAM_PROJECT_NAME_PREFIX = "team project for "
TEAM_PROJECT_NAME_SUFFIX = ""

# Initialized Folder IDs (will be updated after init command)
MAIN_HACKATHON_FOLDER_ID = None
GENERAL_ATTENDEES_FOLDER_ID = None
HACKATHON_TEAMS1_FOLDER_ID = None
HACKATHON_TEAMS2_FOLDER_ID = None

# 組織政策，用於限制服務和虛擬機器執行個體
ORGANIZATION_POLICY = {
    # 這個限制條件用於定義資源可以建立的地理位置。
    # "allowedValues" (允許的值) 被設為 "in:us-central1-locations"，
    # 這表示所有資源都只能在 us-central1 地區及其管轄的所有區域（zones）中建立。
    # "enforce" (強制執行) 設為 True，代表這個規則會被嚴格執行。
    "constraints/gcp.resourceLocations": {
        "rules": [
            {
                "values": {
                    "allowedValues": ["in:us-central1-locations"]
                },
                "enforce": True,
            }
        ]
    },
    # 這個限制條件用於管理虛擬機器是否可以擁有外部 IP 位址。
    # "allowAll" (全部允許) 設為 True，且 "enforce" (強制執行) 設為 False，
    # 代表預設允許所有虛擬機器擁有外部 IP，但這個規則沒有被強制執行，因此專案層級的設定可以覆寫它。
    "constraints/compute.vmExternalIpAccess": {"rules": [{"allowAll": True, "enforce": False}]},
    # 這個限制條件用於管理虛擬機器是否可以轉發非自身的 IP 封包。
    # "allowAll" (全部允許) 設為 True，且 "enforce" (強制執行) 設為 False，
    # 代表預設允許 IP 轉發，但這個規則沒有被強制執行。
    "constraints/compute.vmInstanceSelfIpForwarding": {"rules": [{"allowAll": True, "enforce": False}]},
    # 這個限制條件用於限制可以從哪些專案中取得映像檔來建立虛擬機器。
    # "allowAll" (全部允許) 設為 True，且 "enforce" (強制執行) 設為 False，
    # 代表預設允許從任何專案取得映像檔，但這個規則沒有被強制執行。
    "constraints/compute.trustedImageProjects": {"rules": [{"allowAll": True, "enforce": False}]},
    # 這個限制條件用於決定在新專案中是否要自動建立預設的虛擬私人雲端 (VPC) 網路。
    # "allowAll" (全部允許) 設為 True，且 "enforce" (強制執行) 設為 False，
    # 代表預設會自動建立預設網路，但這個規則沒有被強制執行。
    "constraints/compute.skipDefaultNetworkCreation": {"rules": [{"allowAll": True, "enforce": False}]},
    # 這個限制條件用於限制是否可以移除共享虛擬私人雲端 (Shared VPC) 專案的留置權 (Lien)。
    # "allowAll" (全部允許) 設為 True，且 "enforce" (強制執行) 設為 False，
    # 代表預設允許移除留置權，但這個規則沒有被強制執行。
    "constraints/compute.restrictXpnProjectLienRemoval": {"rules": [{"allowAll": True, "enforce": False}]},
    # 這個限制條件用於定義在主機維護期間，虛擬機器執行個體的行為。
    # "allowAll" (全部允許) 設為 True，且 "enforce" (強制執行) 設為 False，
    # 代表預設允許在主機維護期間，由系統管理員控制執行個體，但這個規則沒有被強制執行。
    "constraints/compute.instanceAdminOnHostMaintenance": {"rules": [{"allowAll": True, "enforce": False}]},
    # 這個限制條件用於限制可以使用哪些子網路來共享虛擬私人雲端 (Shared VPC)。
    # "allowAll" (全部允許) 設為 True，且 "enforce" (強制執行) 設為 False，
    # 代表預設允許使用任何子網路，但這個規則沒有被強制執行。
    "constraints/compute.restrictSharedVpcSubnetworks": {"rules": [{"allowAll": True, "enforce": False}]},
    # 這個限制條件用於限制哪些專案可以作為共享虛擬私人雲端 (Shared VPC) 的主機專案。
    # "allowAll" (全部允許) 設為 True，且 "enforce" (強制執行) 設為 False，
    # 代表預設允許任何專案作為主機專案，但這個規則沒有被強制執行。
    "constraints/compute.restrictSharedVpcHostProjects": {"rules": [{"allowAll": True, "enforce": False}]},
    # 這個限制條件用於設定新專案是否預設只使用區域級的 DNS。
    # "allowAll" (全部允許) 設為 True，且 "enforce" (強制執行) 設為 False，
    # 代表預設不只使用區域級的 DNS，但這個規則沒有被強制執行。
    "constraints/compute.setNewProjectDefaultToZonalDNSOnly": {"rules": [{"allowAll": True, "enforce": False}]},
    # 這個限制條件用於限制可以使用哪些 Google Cloud 服務。
    # "allowedValues" (允許的值) 中列出了所有允許使用的服務，
    # 這裡包含了 Vertex AI 和一些核心服務。
    # "enforce" (強制執行) 設為 True，代表這個規則會被嚴格執行。
    "constraints/gcp.restrictServiceUsage": {
        "rules": [
            {
                "values": {
                    "allowedValues": [
                        "aiplatform.googleapis.com",
                        "storage.googleapis.com",
                        "bigquery.googleapis.com",
                        "cloudfunctions.googleapis.com",
                        "run.googleapis.com",
                        "logging.googleapis.com",
                        "monitoring.googleapis.com",
                        "iam.googleapis.com",
                        "cloudresourcemanager.googleapis.com",
                        "serviceusage.googleapis.com",
                        "cloudbilling.googleapis.com",
                    ]
                },
                "enforce": True,
            }
        ]
    },
    # 這個限制條件用於限制可以建立的虛擬機器類型。
    # "allowedValues" (允許的值) 中列出了所有允許建立的 E2 系列虛擬機器類型，
    # 並且明確指定了它們所在的區域 (us-central1-a, us-central1-b, us-central1-c, us-central1-f)。
    # "enforce" (強制執行) 設為 True，代表這個規則會被嚴格執行。
    "constraints/compute.allowedMachineTypes": {
        "rules": [
            {
                "values": {
                    "allowedValues": ["zones/us-central1-a/machineTypes/e2-medium", "zones/us-central1-a/machineTypes/e2-standard-2", "zones/us-central1-a/machineTypes/e2-standard-4", "zones-us-central1-a/machineTypes/e2-standard-8", "zones/us-central1-b/machineTypes/e2-medium", "zones/us-central1-b/machineTypes/e2-standard-2", "zones/us-central1-b/machineTypes/e2-standard-4", "zones/us-central1-b/machineTypes/e2-standard-8", "zones/us-central1-c/machineTypes/e2-medium", "zones/us-central1-c/machineTypes/e2-standard-2", "zones/us-central1-c/machineTypes/e2-standard-4", "zones/us-central1-c/machineTypes/e2-standard-8", "zones/us-central1-f/machineTypes/e2-medium", "zones/us-central1-f/machineTypes/e2-standard-2", "zones/us-central1-f/machineTypes/e2-standard-4", "zones/us-central1-f/machineTypes/e2-standard-8"]
                },
                "enforce": True,
            }
        ]
    },
}