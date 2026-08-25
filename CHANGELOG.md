# Changelog


# 1.5.0

**Release Date:** 2026-08-25
**Previous Version:** v1.4.1

---

## Highlights

### ⚠️ Breaking Change

- **CLI shortcut renamed: `rg` → `rgt`** to avoid conflicting with ripgrep.
  The full `redgit` command is unchanged. Update shell aliases and scripts accordingly.

### ✨ Features

- New `rgt llm` command group: show, list, set, and inspect LLM providers
- `llm.model` from config is now passed to the Claude Code CLI (`--model`)

### 🐛 Fixes

- Default LLM timeout raised from 120s to 300s (large changesets no longer time out)
- CLI provider timeouts now raise a clear error with a hint to increase `llm.timeout`
- `rgt llm` chat calls now respect `llm.timeout` (previously unbounded)
- CLI providers no longer inherit stdin (prevents hangs in non-interactive runs)

---

# 1.4.1

**Release Date:** 2026-03-30
**Previous Version:** v1.4.0
**Total Commits:** 7

---

## Commit Details

### ✨ Features (3)

- **commit:** enhance proposal and push functionality (`0ec15c8`)
- **cli:** enhance initialization and core functionality (`3dd3333`)
- **utils:** add version checking utility (`5e7ffd3`)

### ♻️ Refactoring (1)

- **integrations:** update base and registry (`7ef8e77`)

### 📚 Documentation (1)

- **readme:** update README and logo (`86c00e5`)

### 🔧 Chores (2)

- **config:** update pyproject.toml (`a4da453`)
- **formula:** update redgit.rb formula (`25e6412`)

---

## Contributors

- **Erman Titiz**: 7 commits (100.0%) `████████████████████`
  - +1113 / -244 lines


---


# 1.3.3

**Release Date:** 2026-01-14
**Previous Version:** v1.3.2
**Total Commits:** 6

---

## Commit Details

### ✨ Features (2)

- **commands:** update push and scout commands (`6b80cc3`)
- **propose:** improve proposal functionality and display (`ecf0ee5`)

### ♻️ Refactoring (1)

- **core:** enhance config and git operations (`9f7587b`)

### 🔧 Chores (3)

- update Homebrew formula and package init (`0f6cd34`)
- update project metadata and dependencies (`d88bdeb`)
- **release:** update changelog and Homebrew formula for v1.3.2 (`c42f656`)

---

## Contributors

- **Erman Titiz**: 6 commits (100.0%) `████████████████████`
  - +1162 / -234 lines


---


# 1.3.2

**Release Date:** 2026-01-07
**Previous Version:** v1.3.1
**Total Commits:** 22

---

## Commit Details

### ✨ Features (14)

- **init:** add initialization command (`22ebf31`)
- **plugin:** update plugin functionality (`8de704d`)
- **notify:** update notification functionality (`9eab6bb`)
- **tunnel:** add tunnel command functionality (`f971ed9`)
- **push:** update push and scout commands (`5ffce95`)
- **poker:** enhance poker functionality with AI voter (`3392ffc`)
- **ci:** update CI, config, and integration commands (`9560801`)
- **webhook:** add webhook functionality with server and actions (`ba95956`)
- **tap:** implement tap functionality with manager (`1b7cb6d`)
- **quality:** add quality checking with Semgrep integration (`cd6fd53`)
- **propose:** enhance propose functionality with analysis and display (`e60e1a3`)
- **daily:** implement daily workflow with state management (`9816c3e`)
- **backup:** add backup command and core functionality (`90f64a4`)
- **quality:** enhance quality and semgrep checks (`6494e81`)

### ♻️ Refactoring (1)

- **core:** move core modules to common directory (`99c34af`)

### 📚 Documentation (1)

- update documentation and project files (`d7dfa52`)

### 🧪 Tests (1)

- update tests for all new functionality (`71246df`)

### 🔧 Chores (5)

- final cleanup and verification (`a997f01`)
- **common:** initialize common module structure (`530d7a8`)
- **utils:** update formatting utilities (`f56f4d0`)
- **cli:** update CLI and main module (`35e05df`)
- **release:** update changelog for v1.3.1 (`74f728d`)

---

## Contributors

- **Erman Titiz**: 22 commits (100.0%) `████████████████████`
  - +9763 / -5771 lines


---


# 1.3.1

**Release Date:** 2025-12-28
**Previous Version:** v1.3.0
**Total Commits:** 12

---

## Commit Details

### ✨ Features (5)

- **core:** add core actions and dependency utilities (`084003a`)
- **webhook:** implement webhook system with notifications (`7f569b8`)
- **tunnel:** add tunnel functionality for secure connections (`8069583`)
- **poker:** implement planning poker with AI voting (`fee4d58`)
- add propose command and update constants (`6721cd7`)

### ♻️ Refactoring (1)

- **integration:** update command implementation (`f5bfc58`)

### 📚 Documentation (2)

- add and update documentation for new features (`eaccef6`)
- update changelog for v1.3.0 (`90b723b`)

### 🧪 Tests (2)

- **cli:** update integration tests (`0b938ca`)
- update push command tests (`ea59a15`)

### 🔧 Chores (2)

- update README and logo (`8096305`)
- **cli:** update CLI and application metadata (`f6c4def`)

---

## Contributors

- **Erman Titiz**: 12 commits (100.0%) `████████████████████`
  - +9042 / -479 lines


---


# 1.3.0

**Release Date:** 2025-12-27
**Previous Version:** v1.2.2
**Total Commits:** 43

---

## Commit Details

### ✨ Features (13)

- **core:** update prompt module (`7f7ae59`)
- **core:** update LLM module (`bd572d5`)
- **core:** update git operations module (`35b1b16`)
- **core:** update config module (`dd6de60`)
- **commands:** update push command (`06523e5`)
- **commands:** update propose command (`25d739f`)
- **cli:** update CLI module (`b7a115a`)
- **utils:** add notification utilities (`43c5bf8`)
- **utils:** add logging utilities (`5dc756f`)
- **utils:** add formatting utilities (`2a832b9`)
- **prompt:** add task filtered commit prompt (`9e00a72`)
- **core:** add constants module (`57328cd`)
- **plugins:** enhance plugin registry and CLI integration (`2d107cb`)

### 📚 Documentation (4)

- update workflows documentation (`c09ac12`)
- update commands documentation (`e53c430`)
- update README documentation (`b1c345b`)
- update README and refresh logo (`2095217`)

### 🧪 Tests (19)

- **unit:** add security unit tests (`0ee7f0a`)
- **unit:** add quality unit tests (`1bdb8bb`)
- **unit:** add push command unit tests (`5ca58f7`)
- **unit:** add propose command unit tests (`efc3db4`)
- **unit:** add prompt unit tests (`23869aa`)
- **unit:** add logging unit tests (`826f53f`)
- **unit:** add LLM unit tests (`9444bfa`)
- **unit:** add base integrations unit tests (`aefb759`)
- **unit:** add integration command unit tests (`fc594b0`)
- **unit:** add init command unit tests (`92fc631`)
- **unit:** add git operations unit tests (`e34992b`)
- **unit:** add daily command unit tests (`1defedb`)
- **unit:** add config unit tests (`7af08ad`)
- **unit:** add CI unit tests (`6a902a3`)
- add unit test package initialization (`8c62a23`)
- **integration:** add CLI integration tests (`fed43a9`)
- add integration test package initialization (`c6e7e2f`)
- add test configuration (`0766b32`)
- add test package initialization (`8663529`)

### 🔧 Chores (7)

- update package initialization (`710226e`)
- **build:** update project dependencies (`d20eba9`)
- **assets:** update logo asset (`39f2bf3`)
- **build:** update Homebrew formula (`b53853a`)
- **ci:** add GitHub Actions test workflow (`f8f59b8`)
- update changelog for v1.2.2 (`d5e217c`)
- **release:** prepare v1.2.2 with changelog and dependency updates (`3210df5`)

---

## Contributors

- **Erman Titiz**: 43 commits (100.0%) `████████████████████`
  - +13654 / -589 lines


---


# 1.2.2

**Release Date:** 2025-12-25
**Previous Version:** v1.2.0
**Total Commits:** 11

---

## Commit Details

### ✨ Features (3)

- **plugins:** enhance plugin registry and CLI integration (`2d107cb`)
- **cli:** enhance CLI commands and integration (`4f92300`)
- **daily:** add daily workflow functionality (`5f5e70d`)

### ♻️ Refactoring (2)

- **integration:** update base integration functionality (`815a71b`)
- **core:** update core configuration and git operations (`17064e0`)

### 📚 Documentation (4)

- update README and refresh logo (`2095217`)
- update README and logo (`f854118`)
- update main changelog (`2180564`)
- add changelog files for v1.2.0 and v1.2.1 (`7ed9977`)

### 🔧 Chores (2)

- **release:** prepare v1.2.2 with changelog and dependency updates (`3210df5`)
- update project configuration and dependencies (`da80660`)

---

## Contributors

- **Erman Titiz**: 11 commits (100.0%) `████████████████████`
  - +2560 / -83 lines


---


# 1.2.2

**Release Date:** 2025-12-25
**Previous Version:** v1.2.0
**Total Commits:** 8

---

## Commit Details

### ✨ Features (2)

- **cli:** enhance CLI commands and integration (`4f92300`)
- **daily:** add daily workflow functionality (`5f5e70d`)

### ♻️ Refactoring (2)

- **integration:** update base integration functionality (`815a71b`)
- **core:** update core configuration and git operations (`17064e0`)

### 📚 Documentation (3)

- update README and logo (`f854118`)
- update main changelog (`2180564`)
- add changelog files for v1.2.0 and v1.2.1 (`7ed9977`)

### 🔧 Chores (1)

- update project configuration and dependencies (`da80660`)

---

## Contributors

- **Erman Titiz**: 8 commits (100.0%) `████████████████████`
  - +2449 / -65 lines


---


# 1.2.1

**Release Date:** 2025-12-19
**Previous Version:** v0.3.14
**Total Commits:** 66

---

# Sürüm 1.2.1 Sürüm Notları

## Genel Bakış
Bu sürüm, temel entegrasyon mimarisi, komut seti ve yapılandırma yönetimi konularında önemli geliştirmeler içermektedir. Ana odak noktası kullanıcı deneyimini artırmak ve sistem entegrasyonlarını daha esnek hale getirmektir.

## Öne Çıkanlar
- **Yeni Tap Fonksiyonu**: Eklenti yönetimini kolaylaştıran yeni bir `tap` komutunun eklenmesi ile kullanıcıların farklı araçları sorunsuz entegre etmesi mümkün olmuştur.
- **Scout Entegrasyonu**: Takım yönetimi fonksiyonelliğiyle birlikte Scout entegrasyonunun eklenmesi, işbirliği özelliklerini güçlendirmiştir.
- **Gelişmiş Yapılandırma Yönetimi**: Yapılandırmaların daha esnek ve kullanıcı dostu hale getirilmesi ile kurulum ve başlatma süreçleri iyileştirilmiştir.

## Detaylı Değişiklikler

### Eklenti Yönetimi ve Entegrasyonlar
Yeni `Tap` fonksiyonu ile eklenti yönetimi kolaylaştırılmış ve Scout entegrasyonu takımların işbirliğini destekleyecek şekilde geliştirilmiştir. Ayrıca, GitHub, JIRA ve Scout için kurulum şemaları eklenmiştir, bu sayede farklı platformlara olan bağlantılar daha güvenli ve standart hale gelmiştir.

### Yapılandırma ve Başlatma Süreçleri
Yapılandırma yönetimi yeniden tasarlanarak kullanıcıların projelerini daha esnek şekilde özelleştirmesi sağlanmıştır. Başlatma komutları da yapılandırma seçenekleriyle genişletilerek kurulum süreci sadeleştirilmiştir.

### Kalite Kontrol ve Güvenlik
Semgrep entegrasyonu sayesinde kod kalitesi kontrolü doğrudan komut satırı arayüzü üzerinden yapılabilir hale gelmiştir. Bu gelişme, geliştiricilerin kod kalitesini daha etkin izlemesine yardımcı olmaktadır.

### Komut Satırı Arayüzü Geliştirmeleri
CLI arayüzü yeniden tasarlanarak hem mevcut komutlar geliştirilmiş hem de yeni komutlar (`ci`, `notify`, `tap`) eklenmiştir. Bu değişikliklerle kullanıcı etkileşimi daha hızlı ve verimli hale getirilmiştir.

### Belgelendirme ve Proje Yönetimi
Geniş kapsamlı belgelendirme seti hazırlanmış, okunabilirlik ve kullanıcı dostu olacak şekilde yapılandırılmıştır. Ayrıca, topluluk kılavuzları ve şablonlar eklenerek açık kaynak katkısı teşvik edilmiştir.

## Teknik Notlar
- JIRA entegrasyonu kullanım dışı bırakılmış ve kaldırılmıştır.
- Yeni entegrasyon mimarisi gereği bazı eski entegrasyon dosyaları kaldırılmıştır.
- Homebrew formülü güncellenmiş ve paketleme metadatası yenilenmiştir.

---

## Commit Details

### ✨ Features (25)

- **core:** enhance core functionality with new utilities (`2287a4c`)
- **commands:** enhance core commands with new features (`87a819b`)
- **prompts:** update commit prompts with new templates (`f711fc0`)
- **tap:** implement Tap functionality for plugin management (`4925e76`)
- **scout:** add Scout integration with team management (`60ba5bc`)
- **quality:** enhance quality command functionality (`cbac5bf`)
- **config:** improve configuration management (`738a905`)
- **init:** enhance initialization with config options (`17db9f3`)
- **core:** add semgrep integration for code quality (`386c1b7`)
- **cli:** update CLI interface and core functionality (`d31ac4a`)
- **config:** enhance configuration and initialization (`919b646`)
- **quality:** add quality checking command and template (`ef07d5b`)
- **tap:** implement tap command functionality (`5320a4c`)
- **push:** enhance push command functionality (`42dee1d`)
- **propose:** improve proposal command functionality (`2c3c749`)
- **config:** enhance configuration handling (`ba2a4b2`)
- **commands:** add ci command implementation (`8520e36`)
- **cli:** integrate new commands and improve CLI (`494a9b7`)
- **integrations:** add install schemas for GitHub, JIRA, and Scout (`0939a66`)
- **cli:** add notify and tap commands (`9808c0b`)
- **core:** enhance propose command functionality (`be201c9`)
- **integrations:** enhance integration registry and package info (`a11bd84`)
- **push:** enhance push command capabilities (`594f4ac`)
- **propose:** enhance propose command capabilities (`96236b3`)
- **prompt:** enhance core prompt capabilities (`9cb9998`)

### ♻️ Refactoring (10)

- **base:** update base integration module (`579e062`)
- **plugins:** remove deprecated plugin implementations (`63db581`)
- **integrations:** remove deprecated integrations (`6a3fe01`)
- **integrations:** update base integration and registry (`4651f71`)
- **integrations:** improve integration system architecture (`7dac181`)
- **integration:** restructure JIRA integration (`de88729`)
- **git:** update git operations and integration registry (`6c0e1fe`)
- **jira:** restructure integration module (`2140f9d`)
- **jira:** restructure JIRA integration as module (`0399c00`)
- **jira:** migrate to modular integration structure (`e053556`)

### 📚 Documentation (13)

- update documentation structure and content (`ff52635`)
- update changelog and readme (`b4e0dcb`)
- update project metadata and documentation (`2e45e94`)
- **readme:** add rg_propose and rg_push screenshots (`733add7`)
- update custom integrations guide (`481ad7e`)
- add comprehensive documentation set (`26a4033`)
- update readme and integrations documentation (`2355508`)
- **branding:** update logo and documentation (`42c7f6e`)
- **integrations:** add integration documentation (`c2e6cc2`)
- update README and logo asset (`8ef1270`)
- **jira:** update integration documentation (`0619bd0`)
- **readme:** update to reflect JIRA integration removal (`41505f2`)
- update changelog for v0.3.14 (`ec2c7a0`)

### 🔧 Chores (18)

- **ui:** update project logo (`4429971`)
- **legacy:** remove deprecated prompt and template files (`aeff43d`)
- **build:** update build configuration and package metadata (`d6b07f2`)
- update project metadata and packaging (`cd0fa49`)
- update Homebrew formula for redgit (`e37f50a`)
- **release:** update changelog for v1.0.5 (`bf79d98`)
- add community guidelines and templates (`30e20e4`)
- update readme and remove deprecated docs (`d29e314`)
- **maintenance:** update gitignore and changelog (`79b63bb`)
- **project:** update metadata, packaging and documentation (`b7fa3db`)
- **branding:** update logo and package metadata (`9b26f95`)
- **build:** update Homebrew formula and project metadata (`45f4bff`)
- **project:** update project metadata (`06d9816`)
- update logo and homebrew formula (`a02befb`)
- add Homebrew formula and update README (`2e15d7a`)
- remove JIRA integration and cleanup (`67b8478`)
- update project dependencies in pyproject.toml (`2134bcb`)
- remove jira integration and update llm module (`c3983ea`)

---

## Contributors

- **Erman Titiz**: 66 commits (100.0%) `████████████████████`
  - +20323 / -13120 lines


---


# 1.2.0

**Release Date:** 2025-12-19
**Previous Version:** v0.3.14
**Total Commits:** 66

---

## Commit Details

### ✨ Features (25)

- **core:** enhance core functionality with new utilities (`2287a4c`)
- **commands:** enhance core commands with new features (`87a819b`)
- **prompts:** update commit prompts with new templates (`f711fc0`)
- **tap:** implement Tap functionality for plugin management (`4925e76`)
- **scout:** add Scout integration with team management (`60ba5bc`)
- **quality:** enhance quality command functionality (`cbac5bf`)
- **config:** improve configuration management (`738a905`)
- **init:** enhance initialization with config options (`17db9f3`)
- **core:** add semgrep integration for code quality (`386c1b7`)
- **cli:** update CLI interface and core functionality (`d31ac4a`)
- **config:** enhance configuration and initialization (`919b646`)
- **quality:** add quality checking command and template (`ef07d5b`)
- **tap:** implement tap command functionality (`5320a4c`)
- **push:** enhance push command functionality (`42dee1d`)
- **propose:** improve proposal command functionality (`2c3c749`)
- **config:** enhance configuration handling (`ba2a4b2`)
- **commands:** add ci command implementation (`8520e36`)
- **cli:** integrate new commands and improve CLI (`494a9b7`)
- **integrations:** add install schemas for GitHub, JIRA, and Scout (`0939a66`)
- **cli:** add notify and tap commands (`9808c0b`)
- **core:** enhance propose command functionality (`be201c9`)
- **integrations:** enhance integration registry and package info (`a11bd84`)
- **push:** enhance push command capabilities (`594f4ac`)
- **propose:** enhance propose command capabilities (`96236b3`)
- **prompt:** enhance core prompt capabilities (`9cb9998`)

### ♻️ Refactoring (10)

- **base:** update base integration module (`579e062`)
- **plugins:** remove deprecated plugin implementations (`63db581`)
- **integrations:** remove deprecated integrations (`6a3fe01`)
- **integrations:** update base integration and registry (`4651f71`)
- **integrations:** improve integration system architecture (`7dac181`)
- **integration:** restructure JIRA integration (`de88729`)
- **git:** update git operations and integration registry (`6c0e1fe`)
- **jira:** restructure integration module (`2140f9d`)
- **jira:** restructure JIRA integration as module (`0399c00`)
- **jira:** migrate to modular integration structure (`e053556`)

### 📚 Documentation (13)

- update documentation structure and content (`ff52635`)
- update changelog and readme (`b4e0dcb`)
- update project metadata and documentation (`2e45e94`)
- **readme:** add rg_propose and rg_push screenshots (`733add7`)
- update custom integrations guide (`481ad7e`)
- add comprehensive documentation set (`26a4033`)
- update readme and integrations documentation (`2355508`)
- **branding:** update logo and documentation (`42c7f6e`)
- **integrations:** add integration documentation (`c2e6cc2`)
- update README and logo asset (`8ef1270`)
- **jira:** update integration documentation (`0619bd0`)
- **readme:** update to reflect JIRA integration removal (`41505f2`)
- update changelog for v0.3.14 (`ec2c7a0`)

### 🔧 Chores (18)

- **ui:** update project logo (`4429971`)
- **legacy:** remove deprecated prompt and template files (`aeff43d`)
- **build:** update build configuration and package metadata (`d6b07f2`)
- update project metadata and packaging (`cd0fa49`)
- update Homebrew formula for redgit (`e37f50a`)
- **release:** update changelog for v1.0.5 (`bf79d98`)
- add community guidelines and templates (`30e20e4`)
- update readme and remove deprecated docs (`d29e314`)
- **maintenance:** update gitignore and changelog (`79b63bb`)
- **project:** update metadata, packaging and documentation (`b7fa3db`)
- **branding:** update logo and package metadata (`9b26f95`)
- **build:** update Homebrew formula and project metadata (`45f4bff`)
- **project:** update project metadata (`06d9816`)
- update logo and homebrew formula (`a02befb`)
- add Homebrew formula and update README (`2e15d7a`)
- remove JIRA integration and cleanup (`67b8478`)
- update project dependencies in pyproject.toml (`2134bcb`)
- remove jira integration and update llm module (`c3983ea`)

---

## Contributors

- **Erman Titiz**: 66 commits (100.0%) `████████████████████`
  - +20323 / -13120 lines


---


# 1.2.0

**Release Date:** 2025-12-19

**Commits:** 233

---

## ✨ Features

- **core:** enhance core functionality with new utilities (`2287a4c`)
- **commands:** enhance core commands with new features (`87a819b`)
- **prompts:** update commit prompts with new templates (`f711fc0`)
- **tap:** implement Tap functionality for plugin management (`4925e76`)
- **scout:** add Scout integration with team management (`60ba5bc`)
- **quality:** enhance quality command functionality (`cbac5bf`)
- **config:** improve configuration management (`738a905`)
- **init:** enhance initialization with config options (`17db9f3`)
- **core:** add semgrep integration for code quality (`386c1b7`)
- **cli:** update CLI interface and core functionality (`d31ac4a`)
- **config:** enhance configuration and initialization (`919b646`)
- **quality:** add quality checking command and template (`ef07d5b`)
- **tap:** implement tap command functionality (`5320a4c`)
- **push:** enhance push command functionality (`42dee1d`)
- **propose:** improve proposal command functionality (`2c3c749`)
- **config:** enhance configuration handling (`ba2a4b2`)
- **commands:** add ci command implementation (`8520e36`)
- **cli:** integrate new commands and improve CLI (`494a9b7`)
- **integrations:** add install schemas for GitHub, JIRA, and Scout (`0939a66`)
- **cli:** add notify and tap commands (`9808c0b`)
- **core:** enhance propose command functionality (`be201c9`)
- **integrations:** enhance integration registry and package info (`a11bd84`)
- **push:** enhance push command capabilities (`594f4ac`)
- **propose:** enhance propose command capabilities (`96236b3`)
- **prompt:** enhance core prompt capabilities (`9cb9998`)
- **integrations:** add JIRA integration support (`e9a439e`)
- **integrations:** add Scout integration support (`f148511`)
- **cli:** enhance propose and push command functionality (`a9f2cb1`)
- **core:** enhance git operations and library initialization (`a321469`)
- add version plugin and enhance git operations (`fbca50e`)
- add splash screen with red-kit asset (`8376d3c`)
- implement plugin system with changelog and version plugins (`4831662`)
- **propose:** auto-initialize git repo when not in one (`4f44787`)
- **cli:** add --version/-v flag to show version (`7e33d6e`)
- **propose:** auto-initialize git repo when not in repository (`fe2701a`)
- **cli:** add --version/-v flag to show version (`cdc5b7b`)
- **propose:** auto-initialize git repo when not in a repository (`2c463a9`)
- **cli:** add --version/-v flag to show version info (`fd8be94`)
- **propose:** auto-initialize git repo when not in one (`68894ec`)
- **cli:** add --version/-v flag to show version (`a5204fa`)

## ♻️ Refactoring

- **base:** update base integration module (`579e062`)
- **plugins:** remove deprecated plugin implementations (`63db581`)
- **integrations:** remove deprecated integrations (`6a3fe01`)
- **integrations:** update base integration and registry (`4651f71`)
- **integrations:** improve integration system architecture (`7dac181`)
- **integration:** restructure JIRA integration (`de88729`)
- **git:** update git operations and integration registry (`6c0e1fe`)
- **jira:** restructure integration module (`2140f9d`)
- **jira:** restructure JIRA integration as module (`0399c00`)
- **jira:** migrate to modular integration structure (`e053556`)
- **cli:** update CLI and core functionality (`f5f3b10`)
- **integrations:** update integration system and registry (`f2660d3`)
- **llm:** simplify Qwen CLI execution (`6f1938b`)
- **gitops:** improve handling of new repos and branch isolation (`e6fbcfe`)
- **llm:** simplify Qwen CLI execution (`5ac9c4b`)
- **gitops:** improve handling of new and empty repositories (`114b3d9`)
- **llm:** simplify Qwen CLI execution (`8638bc0`)
- **gitops:** improve handling of new and existing repositories (`d9262d7`)
- **llm:** simplify Qwen CLI execution (`ff2b979`)
- **gitops:** improve handling of new and non-git repos (`f313d1b`)
- **llm:** simplify Qwen CLI execution (`9a19a40`)

## 📚 Documentation

- update documentation structure and content (`ff52635`)
- update changelog and readme (`b4e0dcb`)
- update project metadata and documentation (`2e45e94`)
- **readme:** add rg_propose and rg_push screenshots (`733add7`)
- update custom integrations guide (`481ad7e`)
- add comprehensive documentation set (`26a4033`)
- update readme and integrations documentation (`2355508`)
- **branding:** update logo and documentation (`42c7f6e`)
- **integrations:** add integration documentation (`c2e6cc2`)
- update README and logo asset (`8ef1270`)
- **jira:** update integration documentation (`0619bd0`)
- **readme:** update to reflect JIRA integration removal (`41505f2`)
- update changelog for v0.3.14 (`ec2c7a0`)
- update plugin and workflow documentation (`6014b9f`)
- add integration and plugin documentation (`6c36840`)
- **integrations:** rebrand SmartCommit to RetGit (`868ab44`)
- **integrations:** rebrand SmartCommit to RetGit (`96b143d`)
- update references from SmartCommit to RetGit (`a4a217a`)
- update references from SmartCommit/sgc to RetGit/rg (`2a623c2`)
- update references from SmartCommit/sgc to RetGit/rg (`a835eaa`)

## 🔧 Chores

- **ui:** update project logo (`4429971`)
- **legacy:** remove deprecated prompt and template files (`aeff43d`)
- **build:** update build configuration and package metadata (`d6b07f2`)
- update project metadata and packaging (`cd0fa49`)
- update Homebrew formula for redgit (`e37f50a`)
- **release:** update changelog for v1.0.5 (`bf79d98`)
- add community guidelines and templates (`30e20e4`)
- update readme and remove deprecated docs (`d29e314`)
- **maintenance:** update gitignore and changelog (`79b63bb`)
- **project:** update metadata, packaging and documentation (`b7fa3db`)
- **branding:** update logo and package metadata (`9b26f95`)
- **build:** update Homebrew formula and project metadata (`45f4bff`)
- **project:** update project metadata (`06d9816`)
- update logo and homebrew formula (`a02befb`)
- add Homebrew formula and update README (`2e15d7a`)
- remove JIRA integration and cleanup (`67b8478`)
- **assets:** update project logo (`2470a33`)
- update project dependencies in pyproject.toml (`2134bcb`)
- remove jira integration and update llm module (`c3983ea`)
- remove old JIRA implementation and update dependencies (`fa84f2a`)
- update project config and core files (`24b0a75`)
- **build:** update project configuration (`0dea2a3`)
- update project configuration (`e76c25c`)
- **release:** v0.2.2 (`797b5d5`)
- update project logo (`253ec3a`)
- update project metadata and license (`2e330a1`)
- initialize project structure and rename from retgit to redgit (`631985b`)
- bump version to 0.1.9 (`d63ac20`)
- bump version to 0.1.8 (`6466665`)
- bump version to 0.1.8 (`ddb0b50`)
- bump version to 0.1.8 (`91c7bdb`)
- bump version to 0.1.5 (`1f85130`)

## 📝 Other

- Merge feature/refactorbase-update-base-integration-mod (`6193869`)
- Merge feature/choreui-update-project-logo (`d78a76c`)
- Merge feature/chorelegacy-remove-deprecated-prompt-and (`f975833`)
- Merge feature/chorebuild-update-build-configuration-an (`14983a3`)
- Merge feature/featcore-enhance-core-functionality-with (`b5d709d`)
- Merge feature/featcommands-enhance-core-commands-with- (`7c857e5`)
- Merge feature/docs-update-documentation-structure-and- (`1fd11e1`)
- Merge feature/refactorplugins-remove-deprecated-plugin (`290eb01`)
- Merge feature/refactorintegrations-remove-deprecated-i (`9beb874`)
- Merge feature/featprompts-update-commit-prompts-with-n (`3b357b1`)
- Merge feature/feattap-implement-tap-functionality-for- (`aeaf239`)
- Merge feature/featscout-add-scout-integration-with-tea (`be81887`)
- Merge feature/featquality-enhance-quality-command-func (`0263acf`)
- Merge feature/docs-update-changelog-and-readme (`de44230`)
- Merge feature/chore-update-project-metadata-and-packag (`06bd98d`)
- Merge feature/chore-update-homebrew-formula-for-redgit (`c23b86d`)
- Merge feature/docs-update-project-metadata-and-documen (`573ee87`)
- Merge feature/featconfig-improve-configuration-managem (`9959382`)
- Merge feature/featinit-enhance-initialization-with-con (`5feac5a`)
- Merge feature/featcore-add-semgrep-integration-for-cod (`9e8d9ff`)
- Merge feature/chorerelease-update-changelog-for-v105 (`7cb46a5`)
- Merge feature/docsreadme-add-rgpropose-and-rgpush-scre (`073ca62`)
- Merge feature/chore-add-community-guidelines-and-templ (`058038b`)
- Merge feature/docs-update-custom-integrations-guide (`7879b60`)
- Merge feature/chore-update-readme-and-remove-deprecate (`414128e`)
- Merge feature/docs-add-comprehensive-documentation-set (`b452a86`)
- Merge feature/choremaintenance-update-gitignore-and-ch (`a3eabb4`)
- Merge feature/choreproject-update-metadata-packaging-a (`09e175f`)
- Merge feature/featcli-update-cli-interface-and-core-fu (`b6ab93d`)
- Merge feature/refactorintegrations-update-base-integra (`00d1cc8`)
- Merge feature/featconfig-enhance-configuration-and-ini (`1e1f975`)
- Merge feature/featquality-add-quality-checking-command (`ae7e36f`)
- Merge feature/refactorintegrations-improve-integration (`934294a`)
- Merge feature/feattap-implement-tap-command-functional (`fc2d13d`)
- Merge feature/featpush-enhance-push-command-functional (`029d121`)
- Merge feature/featpropose-improve-proposal-command-fun (`22bf314`)
- Merge feature/docs-update-readme-and-integrations-docu (`3fbbd91`)
- Merge feature/featconfig-enhance-configuration-handlin (`414a31d`)
- Merge feature/featcommands-add-ci-command-implementati (`0db2be1`)
- Merge feature/refactorintegration-restructure-jira-int (`af4ebe9`)
- Merge feature/refactorgit-update-git-operations-and-in (`c1993dd`)
- Merge feature/featcli-integrate-new-commands-and-impro (`a75a0b7`)
- Merge feature/chorebranding-update-logo-and-package-me (`deeb132`)
- Merge feature/chorebuild-update-homebrew-formula-and-p (`438a92b`)
- Merge feature/featintegrations-add-install-schemas-for (`60f8710`)
- Merge feature/featcli-add-notify-and-tap-commands (`caede4e`)
- Merge feature/featcore-enhance-propose-command-functio (`c8dbcb3`)
- Merge feature/docsbranding-update-logo-and-documentati (`45dcca3`)
- Merge feature/choreproject-update-project-metadata (`e3c11ed`)
- Merge feature/refactorjira-restructure-integration-mod (`40689e4`)
- Merge feature/chore-update-logo-and-homebrew-formula (`837879e`)
- Merge feature/featintegrations-enhance-integration-reg (`421d89e`)
- Merge feature/refactorjira-restructure-jira-integratio (`bf640ea`)
- Merge feature/docsintegrations-add-integration-documen (`16ddde5`)
- Merge feature/chore-add-homebrew-formula-and-update-re (`cc13b5c`)
- Merge feature/docs-update-readme-and-logo-asset (`25fda52`)
- Merge feature/chore-remove-jira-integration-and-cleanu (`4501888`)
- Merge feature/choreassets-update-project-logo (`01fe6f4`)
- Merge feature/featpush-enhance-push-command-capabiliti (`9f6e6d0`)
- Merge feature/featpropose-enhance-propose-command-capa (`3e8344e`)
- Merge feature/featprompt-enhance-core-prompt-capabilit (`eaddda8`)
- Merge feature/docsjira-update-integration-documentatio (`beb548c`)
- Merge feature/chore-update-project-dependencies-in-pyp (`afea7f6`)
- Merge feature/refactorjira-migrate-to-modular-integrat (`8e67d61`)
- Merge feature/chore-remove-jira-integration-and-update (`ddbb290`)
- Merge feature/docsreadme-update-to-reflect-jira-integr (`042a816`)
- Merge feature/docs-update-changelog-for-v0314 (`7b13fdf`)
- Merge feature/chore-remove-old-jira-implementation-and (`dbad5a9`)
- Merge feature/refactorcli-update-cli-and-core-function (`ecf4856`)
- Merge feature/refactorintegrations-update-integration- (`3a935ef`)
- Merge feature/featintegrations-add-jira-integration-su (`4db6987`)
- Merge feature/featintegrations-add-scout-integration-s (`37dcbd1`)
- Merge feature/chore-update-project-config-and-core-fil (`7532b3d`)
- Merge feature/docs-update-plugin-and-workflow-document (`7568e96`)
- Merge feature/chorebuild-update-project-configuration (`8861072`)
- Merge feature/featcli-enhance-propose-and-push-command (`4714bb2`)
- Merge feature/featcore-enhance-git-operations-and-libr (`707633e`)
- Merge feature/feat-add-version-plugin-and-enhance-git- (`193063b`)
- Merge feature/chore-update-project-configuration (`1f245cc`)
- Merge feature/feat-add-splash-screen-with-redkit-asset (`e1c7104`)
- removed files from old named folder (`a0c9a21`)
- Merge branch 'feature/chore-update-project-logo' (`f81f486`)
- Merge branch 'feature/chore-update-project-metadata-and-licens' (`3371241`)
- Merge branch 'feature/feat-implement-plugin-system-with-change' (`247199e`)
- Merge branch 'feature/docs-add-integration-and-plugin-document' (`90a8127`)
- Merge branch 'feature/chore-initialize-project-structure-and-r' (`cc58dfc`)
- Merge branch 'feature/docsintegrations-rebrand-smartcommit-to-' (`65aa3a0`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`71a6a5b`)
- Merge branch 'feature/refactorgitops-improve-handling-of-new-r' (`430ed2a`)
- Merge branch 'feature/featpropose-autoinitialize-git-repo-when' (`b08187b`)
- Merge branch 'feature/featcli-add-versionv-flag-to-show-versio' (`ba3bbbe`)
- Merge branch 'feature/chore-bump-version-to-019' (`87137af`)
- Merge branch 'feature/docsintegrations-rebrand-smartcommit-to-' (`5b03604`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`4c75472`)
- Merge branch 'feature/refactorgitops-improve-handling-of-new-a' (`da91ca5`)
- Merge branch 'feature/featpropose-autoinitialize-git-repo-when' (`df0d935`)
- Merge branch 'feature/featcli-add-versionv-flag-to-show-versio' (`7468bec`)
- Merge branch 'feature/chore-bump-version-to-018' (`353526f`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`1aca5d8`)
- Merge branch 'feature/refactorgitops-improve-handling-of-new-a' (`de95091`)
- Merge branch 'feature/featpropose-autoinitialize-git-repo-when' (`2b6a4da`)
- Merge branch 'feature/featcli-add-versionv-flag-to-show-versio' (`9eed8ed`)
- Merge branch 'feature/chore-bump-version-to-018' (`5951997`)
- Merge branch 'feature/docs-update-references-from-smartcommit-' (`bd1b511`)
- Merge branch 'feature/docs-update-references-from-smartcommits' (`97682d9`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`49724fd`)
- Merge branch 'feature/refactorgitops-improve-handling-of-new-a' (`bb8ab7f`)
- Merge branch 'feature/featpropose-autoinitialize-git-repo-when' (`27d8f5b`)
- Merge branch 'feature/featcli-add-versionv-flag-to-show-versio' (`620e798`)
- Merge branch 'feature/chore-bump-version-to-018' (`fa54dac`)
- Merge branch 'feature/chore-bump-version-to-015' (`b0ed75d`)
- Merge branch 'feature/docs-update-references-from-smartcommits' (`afe1527`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`b110e60`)
- Fix clone directory name in README (`f2d35cf`)
- Add Red Kit mascot to README footer (`1b42b7b`)
- Add retro-style logo and badges to README (`ec1ea4a`)
- Rename package from smart_commit to retgit (`8a91c63`)
- Update GitHub URLs to retgit (`66bff7b`)
- Rename to RetGit, publish to PyPI v0.1.0 (`ddb783a`)
- Initial release v0.1.0 (`ef0f453`)


---


# 1.1.4

**Release Date:** 2025-12-11

---

## 🐛 Fixes

- **quality report:** Now runs Semgrep on all changed files (not just Python)
- **quality report:** Fixed inconsistency where `rg quality scan` found issues but `rg quality report` showed "passed"

## ✨ Improvements

- **quality report:** Multi-language support - Semgrep analyzes YAML, JSON, JS, PHP, Go, and 30+ other languages in changed files
- **quality:** Unified analysis across `check`, `report`, and `scan` commands

---

# 1.1.3

**Release Date:** 2025-12-11

---

## 🐛 Fixes

- **quality:** Fix Semgrep scan showing 0 files scanned
- **semgrep:** Fix severity filter (use multiple `--severity` flags instead of comma-separated)
- **semgrep:** Remove `--quiet` flag to get proper `paths.scanned` in JSON output
- **quality:** Fix lint errors (unused imports, f-strings without placeholders)

## ✨ Improvements

- **quality scan:** Show scan summary with file count and language breakdown
- **quality scan:** Better output formatting with "✓ No issues found" message

---

# 1.1.2

**Release Date:** 2025-12-11

---

## 🐛 Fixes

- **quality:** Fix `rg quality scan` command not accepting path argument
- **quality:** Remove callback to eliminate `[FILE]` argument conflict with subcommands
- **quality:** `rg quality` now shows help with available subcommands

## 📦 Commands

- `rg quality check [FILE]` - Check changed files (git diff)
- `rg quality scan [PATH]` - Scan entire project with Semgrep
- `rg quality status` - Show quality settings
- `rg quality report` - Generate detailed report

---

# 1.1.1

**Release Date:** 2025-12-11

---

## ✨ Features

- **quality:** Add `rg quality scan` command for full project Semgrep scanning
  - Scan entire project (not just git changes)
  - Support for custom rule packs and severity filters
  - JSON and text output formats
  - Useful for full project security audits

## 📚 Documentation

- Updated `docs/commands.md` with `rg quality scan` command

---

# 1.1.0

**Release Date:** 2025-12-11

---

## ✨ Features

- **semgrep:** Add Semgrep integration for multi-language static analysis (35+ languages)
- **quality:** Integrate Semgrep with quality checks for comprehensive code analysis
- **config:** Add `rg config semgrep` command for managing Semgrep settings
- **init:** Add Semgrep setup wizard to `rg init` with automatic installation

## 📦 New Commands

- `rg config semgrep` - View and manage Semgrep settings
- `rg config semgrep --enable` - Enable Semgrep analysis (auto-installs if needed)
- `rg config semgrep --install` - Install Semgrep
- `rg config semgrep --add <pack>` - Add rule packs (e.g., `p/security-audit`)
- `rg config semgrep --list-rules` - List available rule packs

## 🌐 Supported Languages (via Semgrep)

Python, JavaScript, TypeScript, Java, Go, C#, C/C++, PHP, Ruby, Rust, Kotlin, Swift, Scala, JSX, JSON, YAML, Bash, Docker, Terraform, HTML, Lua, Solidity, and more...

## 📚 Documentation

- Updated `docs/commands.md` with Semgrep commands
- Updated `docs/configuration.md` with Semgrep config options
- Updated `README.md` with Semgrep feature

---

# 1.0.5

**Release Date:** 2025-12-11

**Commits:** 191

---

## ✨ Features

- **cli:** update CLI interface and core functionality (`d31ac4a`)
- **config:** enhance configuration and initialization (`919b646`)
- **quality:** add quality checking command and template (`ef07d5b`)
- **tap:** implement tap command functionality (`5320a4c`)
- **push:** enhance push command functionality (`42dee1d`)
- **propose:** improve proposal command functionality (`2c3c749`)
- **config:** enhance configuration handling (`ba2a4b2`)
- **commands:** add ci command implementation (`8520e36`)
- **cli:** integrate new commands and improve CLI (`494a9b7`)
- **integrations:** add install schemas for GitHub, JIRA, and Scout (`0939a66`)
- **cli:** add notify and tap commands (`9808c0b`)
- **core:** enhance propose command functionality (`be201c9`)
- **integrations:** enhance integration registry and package info (`a11bd84`)
- **push:** enhance push command capabilities (`594f4ac`)
- **propose:** enhance propose command capabilities (`96236b3`)
- **prompt:** enhance core prompt capabilities (`9cb9998`)
- **integrations:** add JIRA integration support (`e9a439e`)
- **integrations:** add Scout integration support (`f148511`)
- **cli:** enhance propose and push command functionality (`a9f2cb1`)
- **core:** enhance git operations and library initialization (`a321469`)
- add version plugin and enhance git operations (`fbca50e`)
- add splash screen with red-kit asset (`8376d3c`)
- implement plugin system with changelog and version plugins (`4831662`)
- **propose:** auto-initialize git repo when not in one (`4f44787`)
- **cli:** add --version/-v flag to show version (`7e33d6e`)
- **propose:** auto-initialize git repo when not in repository (`fe2701a`)
- **cli:** add --version/-v flag to show version (`cdc5b7b`)
- **propose:** auto-initialize git repo when not in a repository (`2c463a9`)
- **cli:** add --version/-v flag to show version info (`fd8be94`)
- **propose:** auto-initialize git repo when not in one (`68894ec`)
- **cli:** add --version/-v flag to show version (`a5204fa`)

## ♻️ Refactoring

- **integrations:** update base integration and registry (`4651f71`)
- **integrations:** improve integration system architecture (`7dac181`)
- **integration:** restructure JIRA integration (`de88729`)
- **git:** update git operations and integration registry (`6c0e1fe`)
- **jira:** restructure integration module (`2140f9d`)
- **jira:** restructure JIRA integration as module (`0399c00`)
- **jira:** migrate to modular integration structure (`e053556`)
- **cli:** update CLI and core functionality (`f5f3b10`)
- **integrations:** update integration system and registry (`f2660d3`)
- **llm:** simplify Qwen CLI execution (`6f1938b`)
- **gitops:** improve handling of new repos and branch isolation (`e6fbcfe`)
- **llm:** simplify Qwen CLI execution (`5ac9c4b`)
- **gitops:** improve handling of new and empty repositories (`114b3d9`)
- **llm:** simplify Qwen CLI execution (`8638bc0`)
- **gitops:** improve handling of new and existing repositories (`d9262d7`)
- **llm:** simplify Qwen CLI execution (`ff2b979`)
- **gitops:** improve handling of new and non-git repos (`f313d1b`)
- **llm:** simplify Qwen CLI execution (`9a19a40`)

## 📚 Documentation

- **readme:** add rg_propose and rg_push screenshots (`733add7`)
- update custom integrations guide (`481ad7e`)
- add comprehensive documentation set (`26a4033`)
- update readme and integrations documentation (`2355508`)
- **branding:** update logo and documentation (`42c7f6e`)
- **integrations:** add integration documentation (`c2e6cc2`)
- update README and logo asset (`8ef1270`)
- **jira:** update integration documentation (`0619bd0`)
- **readme:** update to reflect JIRA integration removal (`41505f2`)
- update changelog for v0.3.14 (`ec2c7a0`)
- update plugin and workflow documentation (`6014b9f`)
- add integration and plugin documentation (`6c36840`)
- **integrations:** rebrand SmartCommit to RetGit (`868ab44`)
- **integrations:** rebrand SmartCommit to RetGit (`96b143d`)
- update references from SmartCommit to RetGit (`a4a217a`)
- update references from SmartCommit/sgc to RetGit/rg (`2a623c2`)
- update references from SmartCommit/sgc to RetGit/rg (`a835eaa`)

## 🔧 Chores

- add community guidelines and templates (`30e20e4`)
- update readme and remove deprecated docs (`d29e314`)
- **maintenance:** update gitignore and changelog (`79b63bb`)
- **project:** update metadata, packaging and documentation (`b7fa3db`)
- **branding:** update logo and package metadata (`9b26f95`)
- **build:** update Homebrew formula and project metadata (`45f4bff`)
- **project:** update project metadata (`06d9816`)
- update logo and homebrew formula (`a02befb`)
- add Homebrew formula and update README (`2e15d7a`)
- remove JIRA integration and cleanup (`67b8478`)
- **assets:** update project logo (`2470a33`)
- update project dependencies in pyproject.toml (`2134bcb`)
- remove jira integration and update llm module (`c3983ea`)
- remove old JIRA implementation and update dependencies (`fa84f2a`)
- update project config and core files (`24b0a75`)
- **build:** update project configuration (`0dea2a3`)
- update project configuration (`e76c25c`)
- **release:** v0.2.2 (`797b5d5`)
- update project logo (`253ec3a`)
- update project metadata and license (`2e330a1`)
- initialize project structure and rename from retgit to redgit (`631985b`)
- bump version to 0.1.9 (`d63ac20`)
- bump version to 0.1.8 (`6466665`)
- bump version to 0.1.8 (`ddb0b50`)
- bump version to 0.1.8 (`91c7bdb`)
- bump version to 0.1.5 (`1f85130`)

## 📝 Other

- Merge feature/docsreadme-add-rgpropose-and-rgpush-scre (`073ca62`)
- Merge feature/chore-add-community-guidelines-and-templ (`058038b`)
- Merge feature/docs-update-custom-integrations-guide (`7879b60`)
- Merge feature/chore-update-readme-and-remove-deprecate (`414128e`)
- Merge feature/docs-add-comprehensive-documentation-set (`b452a86`)
- Merge feature/choremaintenance-update-gitignore-and-ch (`a3eabb4`)
- Merge feature/choreproject-update-metadata-packaging-a (`09e175f`)
- Merge feature/featcli-update-cli-interface-and-core-fu (`b6ab93d`)
- Merge feature/refactorintegrations-update-base-integra (`00d1cc8`)
- Merge feature/featconfig-enhance-configuration-and-ini (`1e1f975`)
- Merge feature/featquality-add-quality-checking-command (`ae7e36f`)
- Merge feature/refactorintegrations-improve-integration (`934294a`)
- Merge feature/feattap-implement-tap-command-functional (`fc2d13d`)
- Merge feature/featpush-enhance-push-command-functional (`029d121`)
- Merge feature/featpropose-improve-proposal-command-fun (`22bf314`)
- Merge feature/docs-update-readme-and-integrations-docu (`3fbbd91`)
- Merge feature/featconfig-enhance-configuration-handlin (`414a31d`)
- Merge feature/featcommands-add-ci-command-implementati (`0db2be1`)
- Merge feature/refactorintegration-restructure-jira-int (`af4ebe9`)
- Merge feature/refactorgit-update-git-operations-and-in (`c1993dd`)
- Merge feature/featcli-integrate-new-commands-and-impro (`a75a0b7`)
- Merge feature/chorebranding-update-logo-and-package-me (`deeb132`)
- Merge feature/chorebuild-update-homebrew-formula-and-p (`438a92b`)
- Merge feature/featintegrations-add-install-schemas-for (`60f8710`)
- Merge feature/featcli-add-notify-and-tap-commands (`caede4e`)
- Merge feature/featcore-enhance-propose-command-functio (`c8dbcb3`)
- Merge feature/docsbranding-update-logo-and-documentati (`45dcca3`)
- Merge feature/choreproject-update-project-metadata (`e3c11ed`)
- Merge feature/refactorjira-restructure-integration-mod (`40689e4`)
- Merge feature/chore-update-logo-and-homebrew-formula (`837879e`)
- Merge feature/featintegrations-enhance-integration-reg (`421d89e`)
- Merge feature/refactorjira-restructure-jira-integratio (`bf640ea`)
- Merge feature/docsintegrations-add-integration-documen (`16ddde5`)
- Merge feature/chore-add-homebrew-formula-and-update-re (`cc13b5c`)
- Merge feature/docs-update-readme-and-logo-asset (`25fda52`)
- Merge feature/chore-remove-jira-integration-and-cleanu (`4501888`)
- Merge feature/choreassets-update-project-logo (`01fe6f4`)
- Merge feature/featpush-enhance-push-command-capabiliti (`9f6e6d0`)
- Merge feature/featpropose-enhance-propose-command-capa (`3e8344e`)
- Merge feature/featprompt-enhance-core-prompt-capabilit (`eaddda8`)
- Merge feature/docsjira-update-integration-documentatio (`beb548c`)
- Merge feature/chore-update-project-dependencies-in-pyp (`afea7f6`)
- Merge feature/refactorjira-migrate-to-modular-integrat (`8e67d61`)
- Merge feature/chore-remove-jira-integration-and-update (`ddbb290`)
- Merge feature/docsreadme-update-to-reflect-jira-integr (`042a816`)
- Merge feature/docs-update-changelog-for-v0314 (`7b13fdf`)
- Merge feature/chore-remove-old-jira-implementation-and (`dbad5a9`)
- Merge feature/refactorcli-update-cli-and-core-function (`ecf4856`)
- Merge feature/refactorintegrations-update-integration- (`3a935ef`)
- Merge feature/featintegrations-add-jira-integration-su (`4db6987`)
- Merge feature/featintegrations-add-scout-integration-s (`37dcbd1`)
- Merge feature/chore-update-project-config-and-core-fil (`7532b3d`)
- Merge feature/docs-update-plugin-and-workflow-document (`7568e96`)
- Merge feature/chorebuild-update-project-configuration (`8861072`)
- Merge feature/featcli-enhance-propose-and-push-command (`4714bb2`)
- Merge feature/featcore-enhance-git-operations-and-libr (`707633e`)
- Merge feature/feat-add-version-plugin-and-enhance-git- (`193063b`)
- Merge feature/chore-update-project-configuration (`1f245cc`)
- Merge feature/feat-add-splash-screen-with-redkit-asset (`e1c7104`)
- removed files from old named folder (`a0c9a21`)
- Merge branch 'feature/chore-update-project-logo' (`f81f486`)
- Merge branch 'feature/chore-update-project-metadata-and-licens' (`3371241`)
- Merge branch 'feature/feat-implement-plugin-system-with-change' (`247199e`)
- Merge branch 'feature/docs-add-integration-and-plugin-document' (`90a8127`)
- Merge branch 'feature/chore-initialize-project-structure-and-r' (`cc58dfc`)
- Merge branch 'feature/docsintegrations-rebrand-smartcommit-to-' (`65aa3a0`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`71a6a5b`)
- Merge branch 'feature/refactorgitops-improve-handling-of-new-r' (`430ed2a`)
- Merge branch 'feature/featpropose-autoinitialize-git-repo-when' (`b08187b`)
- Merge branch 'feature/featcli-add-versionv-flag-to-show-versio' (`ba3bbbe`)
- Merge branch 'feature/chore-bump-version-to-019' (`87137af`)
- Merge branch 'feature/docsintegrations-rebrand-smartcommit-to-' (`5b03604`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`4c75472`)
- Merge branch 'feature/refactorgitops-improve-handling-of-new-a' (`da91ca5`)
- Merge branch 'feature/featpropose-autoinitialize-git-repo-when' (`df0d935`)
- Merge branch 'feature/featcli-add-versionv-flag-to-show-versio' (`7468bec`)
- Merge branch 'feature/chore-bump-version-to-018' (`353526f`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`1aca5d8`)
- Merge branch 'feature/refactorgitops-improve-handling-of-new-a' (`de95091`)
- Merge branch 'feature/featpropose-autoinitialize-git-repo-when' (`2b6a4da`)
- Merge branch 'feature/featcli-add-versionv-flag-to-show-versio' (`9eed8ed`)
- Merge branch 'feature/chore-bump-version-to-018' (`5951997`)
- Merge branch 'feature/docs-update-references-from-smartcommit-' (`bd1b511`)
- Merge branch 'feature/docs-update-references-from-smartcommits' (`97682d9`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`49724fd`)
- Merge branch 'feature/refactorgitops-improve-handling-of-new-a' (`bb8ab7f`)
- Merge branch 'feature/featpropose-autoinitialize-git-repo-when' (`27d8f5b`)
- Merge branch 'feature/featcli-add-versionv-flag-to-show-versio' (`620e798`)
- Merge branch 'feature/chore-bump-version-to-018' (`fa54dac`)
- Merge branch 'feature/chore-bump-version-to-015' (`b0ed75d`)
- Merge branch 'feature/docs-update-references-from-smartcommits' (`afe1527`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`b110e60`)
- Fix clone directory name in README (`f2d35cf`)
- Add Red Kit mascot to README footer (`1b42b7b`)
- Add retro-style logo and badges to README (`ec1ea4a`)
- Rename package from smart_commit to retgit (`8a91c63`)
- Update GitHub URLs to retgit (`66bff7b`)
- Rename to RetGit, publish to PyPI v0.1.0 (`ddb783a`)
- Initial release v0.1.0 (`ef0f453`)


---

# 0.3.14

**Release Date:** 2025-12-08

**Commits:** 99

---

## ✨ Features

- **integrations:** add JIRA integration support (`e9a439e`)
- **integrations:** add Scout integration support (`f148511`)
- **cli:** enhance propose and push command functionality (`a9f2cb1`)
- **core:** enhance git operations and library initialization (`a321469`)
- add version plugin and enhance git operations (`fbca50e`)
- add splash screen with red-kit asset (`8376d3c`)
- implement plugin system with changelog and version plugins (`4831662`)
- **propose:** auto-initialize git repo when not in one (`4f44787`)
- **cli:** add --version/-v flag to show version (`7e33d6e`)
- **propose:** auto-initialize git repo when not in repository (`fe2701a`)
- **cli:** add --version/-v flag to show version (`cdc5b7b`)
- **propose:** auto-initialize git repo when not in a repository (`2c463a9`)
- **cli:** add --version/-v flag to show version info (`fd8be94`)
- **propose:** auto-initialize git repo when not in one (`68894ec`)
- **cli:** add --version/-v flag to show version (`a5204fa`)

## ♻️ Refactoring

- **cli:** update CLI and core functionality (`f5f3b10`)
- **integrations:** update integration system and registry (`f2660d3`)
- **llm:** simplify Qwen CLI execution (`6f1938b`)
- **gitops:** improve handling of new repos and branch isolation (`e6fbcfe`)
- **llm:** simplify Qwen CLI execution (`5ac9c4b`)
- **gitops:** improve handling of new and empty repositories (`114b3d9`)
- **llm:** simplify Qwen CLI execution (`8638bc0`)
- **gitops:** improve handling of new and existing repositories (`d9262d7`)
- **llm:** simplify Qwen CLI execution (`ff2b979`)
- **gitops:** improve handling of new and non-git repos (`f313d1b`)
- **llm:** simplify Qwen CLI execution (`9a19a40`)

## 📚 Documentation

- update plugin and workflow documentation (`6014b9f`)
- add integration and plugin documentation (`6c36840`)
- **integrations:** rebrand SmartCommit to RetGit (`868ab44`)
- **integrations:** rebrand SmartCommit to RetGit (`96b143d`)
- update references from SmartCommit to RetGit (`a4a217a`)
- update references from SmartCommit/sgc to RetGit/rg (`2a623c2`)
- update references from SmartCommit/sgc to RetGit/rg (`a835eaa`)

## 🔧 Chores

- remove old JIRA implementation and update dependencies (`fa84f2a`)
- update project config and core files (`24b0a75`)
- **build:** update project configuration (`0dea2a3`)
- update project configuration (`e76c25c`)
- **release:** v0.2.2 (`797b5d5`)
- update project logo (`253ec3a`)
- update project metadata and license (`2e330a1`)
- initialize project structure and rename from retgit to redgit (`631985b`)
- bump version to 0.1.9 (`d63ac20`)
- bump version to 0.1.8 (`6466665`)
- bump version to 0.1.8 (`ddb0b50`)
- bump version to 0.1.8 (`91c7bdb`)
- bump version to 0.1.5 (`1f85130`)

## 📝 Other

- Merge feature/chore-remove-old-jira-implementation-and (`dbad5a9`)
- Merge feature/refactorcli-update-cli-and-core-function (`ecf4856`)
- Merge feature/refactorintegrations-update-integration- (`3a935ef`)
- Merge feature/featintegrations-add-jira-integration-su (`4db6987`)
- Merge feature/featintegrations-add-scout-integration-s (`37dcbd1`)
- Merge feature/chore-update-project-config-and-core-fil (`7532b3d`)
- Merge feature/docs-update-plugin-and-workflow-document (`7568e96`)
- Merge feature/chorebuild-update-project-configuration (`8861072`)
- Merge feature/featcli-enhance-propose-and-push-command (`4714bb2`)
- Merge feature/featcore-enhance-git-operations-and-libr (`707633e`)
- Merge feature/feat-add-version-plugin-and-enhance-git- (`193063b`)
- Merge feature/chore-update-project-configuration (`1f245cc`)
- Merge feature/feat-add-splash-screen-with-redkit-asset (`e1c7104`)
- removed files from old named folder (`a0c9a21`)
- Merge branch 'feature/chore-update-project-logo' (`f81f486`)
- Merge branch 'feature/chore-update-project-metadata-and-licens' (`3371241`)
- Merge branch 'feature/feat-implement-plugin-system-with-change' (`247199e`)
- Merge branch 'feature/docs-add-integration-and-plugin-document' (`90a8127`)
- Merge branch 'feature/chore-initialize-project-structure-and-r' (`cc58dfc`)
- Merge branch 'feature/docsintegrations-rebrand-smartcommit-to-' (`65aa3a0`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`71a6a5b`)
- Merge branch 'feature/refactorgitops-improve-handling-of-new-r' (`430ed2a`)
- Merge branch 'feature/featpropose-autoinitialize-git-repo-when' (`b08187b`)
- Merge branch 'feature/featcli-add-versionv-flag-to-show-versio' (`ba3bbbe`)
- Merge branch 'feature/chore-bump-version-to-019' (`87137af`)
- Merge branch 'feature/docsintegrations-rebrand-smartcommit-to-' (`5b03604`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`4c75472`)
- Merge branch 'feature/refactorgitops-improve-handling-of-new-a' (`da91ca5`)
- Merge branch 'feature/featpropose-autoinitialize-git-repo-when' (`df0d935`)
- Merge branch 'feature/featcli-add-versionv-flag-to-show-versio' (`7468bec`)
- Merge branch 'feature/chore-bump-version-to-018' (`353526f`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`1aca5d8`)
- Merge branch 'feature/refactorgitops-improve-handling-of-new-a' (`de95091`)
- Merge branch 'feature/featpropose-autoinitialize-git-repo-when' (`2b6a4da`)
- Merge branch 'feature/featcli-add-versionv-flag-to-show-versio' (`9eed8ed`)
- Merge branch 'feature/chore-bump-version-to-018' (`5951997`)
- Merge branch 'feature/docs-update-references-from-smartcommit-' (`bd1b511`)
- Merge branch 'feature/docs-update-references-from-smartcommits' (`97682d9`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`49724fd`)
- Merge branch 'feature/refactorgitops-improve-handling-of-new-a' (`bb8ab7f`)
- Merge branch 'feature/featpropose-autoinitialize-git-repo-when' (`27d8f5b`)
- Merge branch 'feature/featcli-add-versionv-flag-to-show-versio' (`620e798`)
- Merge branch 'feature/chore-bump-version-to-018' (`fa54dac`)
- Merge branch 'feature/chore-bump-version-to-015' (`b0ed75d`)
- Merge branch 'feature/docs-update-references-from-smartcommits' (`afe1527`)
- Merge branch 'feature/refactorllm-simplify-qwen-cli-execution' (`b110e60`)
- Fix clone directory name in README (`f2d35cf`)
- Add Red Kit mascot to README footer (`1b42b7b`)
- Add retro-style logo and badges to README (`ec1ea4a`)
- Rename package from smart_commit to retgit (`8a91c63`)
- Update GitHub URLs to retgit (`66bff7b`)
- Rename to RetGit, publish to PyPI v0.1.0 (`ddb783a`)
- Initial release v0.1.0 (`ef0f453`)

