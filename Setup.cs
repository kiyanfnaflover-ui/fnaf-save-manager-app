using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;
using System.Diagnostics;
using System.Net;
using Microsoft.Win32;

static class SetupProgram
{
    // Native Win32 (WinMM) C API - used to play the installer music (mp3).
    [DllImport("winmm.dll", CharSet = CharSet.Unicode)]
    private static extern int mciSendString(string command, StringBuilder ret, int len, IntPtr hwnd);

    // Native Win32 shell32 API - used to relaunch elevated when needed.
    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    private static extern IntPtr ShellExecute(IntPtr hwnd, string lpOperation,
        string lpFile, string lpParameters, string lpDirectory, int nShowCmd);

    // Native Win32 user32 API - informational "About" MessageBox style is handled by Forms.
    private const string APP_EXE = "fnaf_save_v3.exe";
    private const string APP_NAME = "FNAF Save Manager";
    private const string APP_VERSION = "v4.0";
    private const string PUBLISHER = "K_F_";
    private const string UNINSTALL_KEY = @"Software\Microsoft\Windows\CurrentVersion\Uninstall\FNAF Save Manager";
    private const string MUSIC_ALIAS = "fsmSong";
    private const string APP_RESOURCE = "InstallerApp";
    private const string UPDATE_URL = ""; // optional: e.g. "https://example.com/fsm/latest.txt"

    [STAThread]
    private static void Main(string[] args)
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);

        string presetPath = null;
        bool autoInstall = false;
        bool uninstall = false;
        foreach (string arg in args)
        {
            if (arg.StartsWith("--path=", StringComparison.OrdinalIgnoreCase))
            {
                presetPath = arg.Substring("--path=".Length).Trim().Trim('"');
            }
            else if (string.Equals(arg, "--auto", StringComparison.OrdinalIgnoreCase))
            {
                autoInstall = true;
            }
            else if (string.Equals(arg, "--uninstall", StringComparison.OrdinalIgnoreCase))
            {
                uninstall = true;
            }
        }

        if (uninstall)
        {
            UninstallProgram(presetPath);
            return;
        }

        Application.Run(new InstallerForm(presetPath, autoInstall));
    }

    private static byte[] ReadResource(string name)
    {
        Stream s = null;
        MemoryStream ms = null;
        try
        {
            s = Assembly.GetExecutingAssembly().GetManifestResourceStream(name);
            if (s == null) return null;
            ms = new MemoryStream();
            s.CopyTo(ms);
            return ms.ToArray();
        }
        catch { return null; }
        finally
        {
            if (s != null) s.Dispose();
            if (ms != null) ms.Dispose();
        }
    }

    private static bool IsAdministrator()
    {
        try
        {
            using (var identity = System.Security.Principal.WindowsIdentity.GetCurrent())
            {
                var principal = new System.Security.Principal.WindowsPrincipal(identity);
                return principal.IsInRole(System.Security.Principal.WindowsBuiltInRole.Administrator);
            }
        }
        catch { return false; }
    }

    // --------------------------------------------------------------------- //
    //  standalone uninstaller (invoked from Programs & Features)            //
    // --------------------------------------------------------------------- //
    private static void UninstallProgram(string installDir)
    {
        try { Application.EnableVisualStyles(); } catch { }

        if (string.IsNullOrEmpty(installDir) && File.Exists(Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "Programs", APP_NAME, APP_EXE)))
        {
            installDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "Programs", APP_NAME);
        }
        if (string.IsNullOrEmpty(installDir) || !Directory.Exists(installDir))
        {
            installDir = DefaultInstallDirGuess();
        }

        MessageBox.Show("FNAF Save Manager will now be removed from:\n\n" + installDir,
            "Uninstall " + APP_NAME, MessageBoxButtons.OK, MessageBoxIcon.Information);

        try
        {
            // Close any running copy first.
            foreach (var proc in Process.GetProcessesByName("fnaf_save_v3"))
            {
                try { proc.Kill(); } catch { }
            }

            // Remove desktop / Start Menu shortcuts.
            try { File.Delete(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), APP_NAME + ".lnk")); } catch { }
            try { File.Delete(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Microsoft", "Windows", "Start Menu", "Programs", APP_NAME + ".lnk")); } catch { }

            // Remove the uninstaller registry entry.
            try { Registry.CurrentUser.DeleteSubKeyTree(UNINSTALL_KEY, false); } catch { }

            // Remove app files (keep anything outside our app folder untouched).
            if (Directory.Exists(installDir))
            {
                foreach (string f in Directory.GetFiles(installDir))
                {
                    try { File.Delete(f); } catch { }
                }
                foreach (string sub in Directory.GetDirectories(installDir))
                {
                    try { Directory.Delete(sub, true); } catch { }
                }
                // Remove the now-empty install folder.
                try { Directory.Delete(installDir, true); } catch { }
            }

            MessageBox.Show("FNAF Save Manager has been uninstalled successfully.", "Uninstall Complete",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex)
        {
            MessageBox.Show("Some files could not be removed automatically:\n\n" + ex.Message +
                "\n\nYou can manually delete the folder: " + installDir,
                "Uninstall", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    // It's not possible to delete a folder currently in use by the running Setup.exe,
    // so this helper determines the install dir when none was passed explicitly.
    private static string DefaultInstallDirGuess()
    {
        string local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        if (string.IsNullOrEmpty(local)) local = Path.GetTempPath();
        return Path.Combine(local, "Programs", APP_NAME);
    }

    private sealed class InstallerForm : Form
    {
        // ---- navigation pages ----
        private enum Page { Welcome, License, Location, Components, Install, Complete }
        private Page _page = Page.Welcome;

        private readonly TextBox _pathBox = new TextBox();
        private readonly CheckBox _chkDesktop = new CheckBox();
        private readonly CheckBox _chkStartMenu = new CheckBox();
        private readonly CheckBox _chkLaunch = new CheckBox();
        private readonly CheckBox _chkAutoBackup = new CheckBox();
        private readonly CheckBox _chkMusic = new CheckBox();
        private readonly CheckBox _chkUpdateCheck = new CheckBox();
        private readonly Button _btnNext = new Button();
        private readonly Button _btnBack = new Button();
        private readonly Button _btnInstall = new Button();
        private readonly Button _btnBrowse = new Button();
        private readonly Button _btnCancel = new Button();
        private readonly Label _status = new Label();
        private readonly Label _welcomeText = new Label();
        private readonly Label _locationHelp = new Label();
        private readonly Label _diskInfo = new Label();
        private readonly TextBox _licenseText = new TextBox();
        private readonly ProgressBar _progress = new ProgressBar();
        private readonly RichTextBox _log = new RichTextBox();
        private readonly Label _completeText = new Label();

        private string _musicPath;
        private readonly bool _autoInstall;
        private readonly string _presetPath;
        private string _existingInstall;
        private long _appSizeBytes;
        private string _logPath;

        public InstallerForm(string presetPath, bool autoInstall)
        {
            _autoInstall = autoInstall;
            _presetPath = string.IsNullOrWhiteSpace(presetPath) ? null : presetPath.Trim().TrimEnd('\\', '/');
            BuildUi();
            if (_presetPath != null) _pathBox.Text = _presetPath;
            _existingInstall = FindExistingInstall();
            Shown += OnShown;
            FormClosed += OnClosed;
        }

        private static string DefaultInstallDir()
        {
            string local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            if (string.IsNullOrEmpty(local)) local = Path.GetTempPath();
            return Path.Combine(local, "Programs", APP_NAME);
        }

        private void BuildUi()
        {
            Text = APP_NAME + " " + APP_VERSION + " - Installer";
            ClientSize = new Size(620, 720);
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            BackColor = Color.FromArgb(243, 239, 228);
            ForeColor = Color.FromArgb(40, 36, 30);
            StartPosition = FormStartPosition.CenterScreen;

            byte[] iconBytes = ReadResource("InstallerIcon");
            if (iconBytes != null) { try { Icon = new Icon(new MemoryStream(iconBytes)); } catch { } }

            // banner
            PictureBox banner = new PictureBox();
            banner.Dock = DockStyle.Top;
            banner.Height = 200;
            banner.BorderStyle = BorderStyle.FixedSingle;
            banner.BackColor = Color.FromArgb(30, 26, 22);
            banner.SizeMode = PictureBoxSizeMode.StretchImage;
            byte[] bannerBytes = ReadResource("InstallerBanner");
            if (bannerBytes != null) { try { banner.Image = Image.FromStream(new MemoryStream(bannerBytes)); } catch { } }
            Controls.Add(banner);

            // header line
            Label head = MkLabel(APP_NAME + " " + APP_VERSION + "  —  Setup Wizard", 14, true);
            head.Location = new Point(22, 210);
            head.Size = new Size(576, 26);
            Controls.Add(head);

            int x = 22, w = 576;

            // ---------------- Welcome page ----------------
            _welcomeText.Location = new Point(x, 250);
            _welcomeText.Size = new Size(w, 150);
            _welcomeText.Text =
                "Welcome to the installer for FNAF Save Manager!\n\n" +
                "FNAF Save Manager lets you edit save files across all Five Nights at Freddy's titles:\n" +
                "• Unlock nights & stars\n" +
                "• Edit money, coins and high scores\n" +
                "• Create backups before every change\n" +
                "• Game-by-game progression editor\n\n" +
                "Created by " + PUBLISHER + ". Click Next to begin.";
            _welcomeText.Font = new Font("Segoe UI", 10);
            _welcomeText.Visible = true;
            Controls.Add(_welcomeText);

            // ---------------- License page ----------------
            _licenseText.Location = new Point(x, 250);
            _licenseText.Size = new Size(w, 300);
            _licenseText.Multiline = true;
            _licenseText.ReadOnly = true;
            _licenseText.ScrollBars = ScrollBars.Vertical;
            _licenseText.Text = LicenseText();
            _licenseText.Font = new Font("Consolas", 9);
            _licenseText.Visible = false;
            Controls.Add(_licenseText);

            // ---------------- Location page ----------------
            ReadDiskInfo(); // compute app size before labels exist
            Label locLbl = MkLabel("Choose where FNAF Save Manager will be installed:", 10, false);
            locLbl.Location = new Point(x, 250);
            locLbl.Size = new Size(w, 22);
            locLbl.Visible = false;
            Controls.Add(locLbl);

            _pathBox.Text = DefaultInstallDir();
            _pathBox.Location = new Point(x, 276);
            _pathBox.Size = new Size(w - 96, 24);
            _pathBox.BorderStyle = BorderStyle.Fixed3D;
            _pathBox.Visible = false;
            Controls.Add(_pathBox);

            _btnBrowse.Text = "Browse...";
            _btnBrowse.Location = new Point(x + w - 88, 274);
            _btnBrowse.Size = new Size(88, 28);
            _btnBrowse.FlatStyle = FlatStyle.Flat;
            _btnBrowse.Click += BrowseClick;
            _btnBrowse.Visible = false;
            Controls.Add(_btnBrowse);

            _locationHelp.Location = new Point(x, 306);
            _locationHelp.Size = new Size(w, 30);
            _locationHelp.Text = "";
            _locationHelp.Font = new Font("Segoe UI", 9);
            _locationHelp.Visible = false;
            Controls.Add(_locationHelp);

            _diskInfo.Location = new Point(x, 342);
            _diskInfo.Size = new Size(w, 90);
            _diskInfo.Text = "";
            _diskInfo.Font = new Font("Consolas", 9);
            _diskInfo.Visible = false;
            Controls.Add(_diskInfo);

            // ---------------- Components page ----------------
            Label compHeader = MkLabel("Select additional options:", 10, true);
            compHeader.Location = new Point(x, 250);
            compHeader.Size = new Size(w, 22);
            compHeader.Visible = false;
            Controls.Add(compHeader);

            PositionCheck(_chkDesktop, "Create a desktop shortcut", x, 280);
            _chkDesktop.Checked = true;
            _chkDesktop.Visible = false;
            Controls.Add(_chkDesktop);

            _chkStartMenu.Text = "Create a Start Menu shortcut";
            _chkStartMenu.Checked = true;
            _chkStartMenu.Location = new Point(x, 310);
            _chkStartMenu.Size = new Size(360, 22);
            _chkStartMenu.Visible = false;
            Controls.Add(_chkStartMenu);

            _chkAutoBackup.Text = "Make automatic backups before every save edit";
            _chkAutoBackup.Checked = true;
            _chkAutoBackup.Location = new Point(x, 340);
            _chkAutoBackup.Size = new Size(360, 22);
            _chkAutoBackup.Visible = false;
            Controls.Add(_chkAutoBackup);

            _chkMusic.Text = "Play background music during the installer";
            _chkMusic.Checked = true;
            _chkMusic.Location = new Point(x, 370);
            _chkMusic.Size = new Size(360, 22);
            _chkMusic.Visible = false;
            Controls.Add(_chkMusic);

            _chkUpdateCheck.Text = "Check for updates when an internet connection is available";
            _chkUpdateCheck.Checked = false;
            _chkUpdateCheck.Location = new Point(x, 400);
            _chkUpdateCheck.Size = new Size(360, 22);
            _chkUpdateCheck.Visible = false;
            Controls.Add(_chkUpdateCheck);

            _chkLaunch.Text = "Launch " + APP_NAME + " after installation";
            _chkLaunch.Checked = true;
            _chkLaunch.Location = new Point(x, 430);
            _chkLaunch.Size = new Size(360, 22);
            _chkLaunch.Visible = false;
            Controls.Add(_chkLaunch);

            // ---------------- Install page ----------------
            _progress.Location = new Point(x, 300);
            _progress.Size = new Size(w, 16);
            _progress.Minimum = 0;
            _progress.Maximum = 100;
            _progress.Value = 0;
            _progress.Visible = false;
            Controls.Add(_progress);

            _status.Location = new Point(x, 326);
            _status.Size = new Size(w, 24);
            _status.Text = "";
            _status.Font = new Font("Segoe UI", 9, FontStyle.Bold);
            _status.Visible = false;
            Controls.Add(_status);

            _log.Location = new Point(x, 356);
            _log.Size = new Size(w, 150);
            _log.ReadOnly = true;
            _log.BackColor = Color.FromArgb(24, 22, 20);
            _log.ForeColor = Color.FromArgb(210, 200, 170);
            _log.Font = new Font("Consolas", 8);
            _log.BorderStyle = BorderStyle.FixedSingle;
            _log.Visible = false;
            Controls.Add(_log);

            _completeText.Location = new Point(x, 250);
            _completeText.Size = new Size(w, 180);
            _completeText.Text = "";
            _completeText.Font = new Font("Segoe UI", 10);
            _completeText.Visible = false;
            Controls.Add(_completeText);

            // --------------- footer buttons ---------------
            _btnBack.Text = "< Back";
            _btnBack.Location = new Point(x, 640);
            _btnBack.Size = new Size(90, 32);
            _btnBack.FlatStyle = FlatStyle.Flat;
            _btnBack.Click += (s, e) => Navigate(-1);
            Controls.Add(_btnBack);

            _btnNext.Text = "Next >";
            _btnNext.Location = new Point(x + 100, 640);
            _btnNext.Size = new Size(90, 32);
            _btnNext.FlatStyle = FlatStyle.Flat;
            _btnNext.BackColor = Color.FromArgb(214, 100, 60);
            _btnNext.ForeColor = Color.White;
            _btnNext.Font = new Font(Font.FontFamily, 10, FontStyle.Bold);
            _btnNext.Click += (s, e) => NextPressed();
            Controls.Add(_btnNext);

            _btnInstall.Text = "Install";
            _btnInstall.Location = new Point(x + 100, 640);
            _btnInstall.Size = new Size(90, 32);
            _btnInstall.FlatStyle = FlatStyle.Flat;
            _btnInstall.BackColor = Color.FromArgb(194, 70, 44);
            _btnInstall.ForeColor = Color.White;
            _btnInstall.Font = new Font(Font.FontFamily, 12, FontStyle.Bold);
            _btnInstall.Click += (s, e) => { if (_page == Page.Complete) Close(); else BeginInstall(); };
            _btnInstall.Visible = false;
            Controls.Add(_btnInstall);

            _btnCancel.Text = "Cancel";
            _btnCancel.Location = new Point(x + 200, 640);
            _btnCancel.Size = new Size(90, 32);
            _btnCancel.FlatStyle = FlatStyle.Flat;
            _btnCancel.Click += (s, e) => Close();
            Controls.Add(_btnCancel);

            Label foot = MkLabel("Can install to any drive. Admin rights requested automatically when needed.", 8, false);
            foot.Location = new Point(x, 686);
            foot.Size = new Size(w, 16);
            foot.ForeColor = Color.FromArgb(120, 110, 92);
            Controls.Add(foot);

            ShowPage(Page.Welcome);
        }

        private void PositionCheck(CheckBox box, string text, int x, int y)
        {
            box.Text = text;
            box.Location = new Point(x, y);
            box.Size = new Size(360, 22);
        }

        private void ReadDiskInfo()
        {
            // Compute the embedded app EXE size from the manifest resource.
            _appSizeBytes = 0;
            using (Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream(APP_RESOURCE))
            {
                if (s != null) _appSizeBytes = s.Length;
            }
        }

        private void BrowseClick(object sender, EventArgs e)
        {
            using (FolderBrowserDialog dlg = new FolderBrowserDialog())
            {
                string start = _pathBox.Text;
                if (!Directory.Exists(start)) start = Environment.GetFolderPath(Environment.SpecialFolder.MyComputer);
                dlg.SelectedPath = start;
                if (dlg.ShowDialog(this) == DialogResult.OK)
                {
                    _pathBox.Text = Path.Combine(dlg.SelectedPath, APP_NAME);
                }
            }
            UpdateDiskLabels();
        }

        private void UpdateDiskLabels()
        {
            long required = 5L * 1024 * 1024 + _appSizeBytes; // small overhead + app
            long available = 0;
            string root = "";
            try
            {
                string full = Path.GetFullPath(_pathBox.Text);
                root = Path.GetPathRoot(full);
                if (!string.IsNullOrEmpty(root) && root.Length >= 2)
                {
                    DriveInfo drive = new DriveInfo(root.Substring(0, 1));
                    if (drive.IsReady) available = drive.AvailableFreeSpace;
                }
            }
            catch { }

            string reqText = FormatBytes(required);
            string availText = available > 0 ? FormatBytes(available) : "unknown";
            string ok = (available > required) ? "YES" : "NO";
            _diskInfo.Text =
                "Required disk space:  " + reqText + "\r\n" +
                "Available on " + (string.IsNullOrEmpty(root) ? "drive" : root) + ":  " + availText + "\r\n" +
                "Sufficient space:     " + ok;
        }

        private static string FormatBytes(long b)
        {
            if (b >= 1024L * 1024) return ((double)b / (1024 * 1024)).ToString("0.0") + " MB";
            if (b >= 1024) return ((double)b / 1024).ToString("0.0") + " KB";
            return b + " B";
        }

        private void Navigate(int dir)
        {
            int idx = (int)_page + dir;
            if (idx < 0) idx = 0;
            if (idx > (int)Page.Complete) idx = (int)Page.Complete;
            if (idx == (int)Page.Location)
            {
                _pathBox.Focus();
                UpdateDiskLabels();
            }
            else if (idx == (int)Page.Install)
            {
                // Only install from Next on first entry to Install page.
                ShowPage(Page.Install);
                BeginInstall();
                return;
            }
            ShowPage((Page)idx);
        }

        private void NextPressed()
        {
            if (_page == Page.Welcome)
            {
                ShowPage(Page.License);
            }
            else if (_page == Page.License)
            {
                // license "accepted" implicitly by clicking Next
                ShowPage(Page.Location);
            }
            else if (_page == Page.Location)
            {
                string err = ValidateInstallPath();
                if (err != null)
                {
                    MessageBox.Show(this, err, APP_NAME, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    return;
                }
                ShowPage(Page.Components);
            }
            else if (_page == Page.Components)
            {
                StartInstallFlow();
            }
        }

        private void ShowPage(Page page)
        {
            _page = page;
            PageControls(page);

            bool onInstall = page == Page.Install;
            _btnNext.Visible = !onInstall && page != Page.Complete;
            _btnInstall.Visible = onInstall || page == Page.Complete;
            _btnInstall.Text = (page == Page.Complete) ? "Finish" : "Install";
            _btnBack.Visible = page != Page.Welcome && page != Page.Complete;
            _btnBack.Enabled = page != Page.Install;

            if (page == Page.Welcome)
            {
                if (!string.IsNullOrEmpty(_existingInstall))
                {
                    _welcomeText.Text += "\n\n[=] A previous installation was detected at:\n    " + _existingInstall + "\n    Installing again will repair / update it.";
                }
                _btnNext.Focus();
            }
        }

        private void PageControls(Page page)
        {
            bool welcome = page == Page.Welcome;
            bool license = page == Page.License;
            bool loc = page == Page.Location;
            bool comp = page == Page.Components;
            bool install = page == Page.Install;
            bool complete = page == Page.Complete;

            _welcomeText.Visible = welcome;
            _licenseText.Visible = license;
            _pathBox.Visible = loc;
            _btnBrowse.Visible = loc;
            _locationHelp.Visible = loc;
            _diskInfo.Visible = loc;
            // show components checks
            foreach (Control c in Controls)
            {
                if (c == _chkDesktop || c == _chkStartMenu || c == _chkLaunch || c == _chkAutoBackup || c == _chkMusic || c == _chkUpdateCheck)
                {
                    c.Visible = comp;
                }
            }
            Label locLbl = null; // find the location label control by name
            foreach (Control c in Controls)
            {
                if (c is Label && c.Text.StartsWith("Choose where")) { locLbl = (Label)c; break; }
            }
            if (locLbl != null) locLbl.Visible = loc;

            Label compHeader = FindLabel("Select additional options:");
            if (compHeader != null) compHeader.Visible = comp;

            _progress.Visible = install;
            _status.Visible = install;
            _log.Visible = install;
            _completeText.Visible = complete;
            _btnCancel.Enabled = !install;
        }

        private Label FindLabel(string text)
        {
            foreach (Control c in Controls)
            {
                if (c is Label && c.Text == text) return (Label)c;
            }
            return null;
        }

        // ------------------------------------------------------------------ //
        //  validation                                                          //
        // ------------------------------------------------------------------ //
        private string ValidateInstallPath()
        {
            string dir = (_pathBox.Text ?? "").Trim().TrimEnd('\\', '/');
            if (dir.Length == 0) return "Please choose an install folder.";

            string full, root;
            try { full = Path.GetFullPath(dir); }
            catch (Exception ex) { return "Invalid path: " + ex.Message; }

            root = Path.GetPathRoot(full);
            if (string.IsNullOrEmpty(root) || root.Length < 2)
                return "Please choose a path on a drive, e.g. \"D:\\Games\\" + APP_NAME + "\".";

            try
            {
                DriveInfo drive = new DriveInfo(root.Substring(0, 1));
                if (!drive.IsReady) return "Drive \"" + root + "\" is not ready. Please choose an available drive.";
                if (drive.DriveType == DriveType.CDRom || drive.DriveType == DriveType.Unknown)
                    return "Cannot install to \"" + root + "\" (read-only media). Please pick a disk drive.";
            }
            catch (Exception ex) { return "Could not access drive \"" + root + "\": " + ex.Message; }

            // check free space
            try
            {
                long available = new DriveInfo(root.Substring(0, 1)).AvailableFreeSpace;
                long required = 5L * 1024 * 1024 + _appSizeBytes;
                if (available < required)
                    return "Not enough free space on " + root + ".\n\nRequired: " + FormatBytes(required) +
                        "\nAvailable: " + FormatBytes(available);
            }
            catch { }

            return null;
        }

        // ------------------------------------------------------------------ //
        //  install flow                                                        //
        // ------------------------------------------------------------------ //
        private void StartInstallFlow()
        {
            // Components page -> show install page, run.
            ShowPage(Page.Install);
            BeginInstall();
        }

        private void BeginInstall()
        {
            if (_page != Page.Install) return;
            string err = ValidateInstallPath();
            if (err != null)
            {
                MessageBox.Show(this, err, APP_NAME, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                ShowPage(Page.Location);
                return;
            }

            string installDir = _pathBox.Text.Trim().TrimEnd('\\', '/');

            // Ensure elevation if the target needs admin rights.
            if (!CanWrite(installDir) && !IsAdministrator())
            {
                if (RelaunchElevated(installDir))
                {
                    _status.Text = "Requesting administrator access...";
                    MessageBox.Show(this,
                        "This folder needs administrator rights.\n\nThe installer is restarting with administrator " +
                        "access to install to:\n" + installDir + "\n\nAllow the UAC prompt to continue.",
                        "Administrator Access Needed", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    Close();
                    return;
                }
                MessageBox.Show(this, "Access denied for:\n" + installDir + "\n\nChoose a folder you own or approve the UAC prompt.",
                    APP_NAME, MessageBoxButtons.OK, MessageBoxIcon.Error);
                ShowPage(Page.Location);
                return;
            }

            RunInstall(installDir);
        }

        private bool CanWrite(string dir)
        {
            try
            {
                Directory.CreateDirectory(dir);
                string probe = Path.Combine(dir, ".fsm_write_test");
                using (FileStream fs = new FileStream(probe, FileMode.Create, FileAccess.Write)) { }
                File.Delete(probe);
                return true;
            }
            catch { return false; }
        }

        private bool RelaunchElevated(string installDir)
        {
            try
            {
                string exe = Application.ExecutablePath;
                string args = "--path=\"" + installDir + "\" --auto";
                IntPtr result = ShellExecute(IntPtr.Zero, "runas", exe, args, null, 1);
                return result.ToInt64() > 32;
            }
            catch { return false; }
        }

        private void RunInstall(string installDir)
        {
            _btnInstall.Enabled = false;
            _status.Text = "Checking installation requirements...";
            _log.Clear();
            _logPath = Path.Combine(Path.GetTempPath(), "fsm_install.log");
            try { File.WriteAllText(_logPath, "=== FNAF Save Manager " + APP_VERSION + " install log ===\r\n"); } catch { }
            AppendLog("[INFO] FNAF Save Manager " + APP_VERSION + " install started");
            AppendLog("[INFO] Target: " + installDir);
            Application.DoEvents();

            bool dstCopied = false;
            try
            {
                if (_appSizeBytes <= 0)
                {
                    AppendLog("[ERROR] The application is missing from the installer (embedded resource not found).");
                    MessageBox.Show(this, "The application could not be found inside the installer.", APP_NAME, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    _status.Text = "App missing.";
                    _btnInstall.Enabled = true;
                    return;
                }

                // 1) create folder (already validated writable)
                Directory.CreateDirectory(installDir);
                AppendLog("[OK] Install folder ready");

                // 2) kill any running copy
                _progress.Value = 10;
                _status.Text = "Closing any running copy of the app...";
                foreach (var proc in Process.GetProcessesByName("fnaf_save_v3")) { try { proc.Kill(); } catch { } }
                System.Threading.Thread.Sleep(300);

                // 3) extract embedded app exe with progress
                _status.Text = "Copying application files...";
                string dstExe = Path.Combine(installDir, APP_EXE);
                CopyResourceWithProgress(APP_RESOURCE, dstExe, 10, 70);
                dstCopied = true;
                AppendLog("[OK] Copied " + APP_EXE + " (" + FormatBytes(_appSizeBytes) + ")");

                // 4) shortcuts
                _progress.Value = 75;
                _status.Text = "Creating shortcuts...";
                if (_chkDesktop.Checked) { CreateShortcut(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), dstExe, installDir); AppendLog("[OK] Desktop shortcut"); }
                if (_chkStartMenu.Checked) { CreateShortcut(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Microsoft", "Windows", "Start Menu", "Programs"), dstExe, installDir); AppendLog("[OK] Start Menu shortcut"); }

                // 5) registry uninstaller entry
                _progress.Value = 85;
                _status.Text = "Registering the app with Windows Apps & Features...";
                WriteRegistry(installDir, dstExe);
                AppendLog("[OK] Registered uninstaller entry");

                // 6) settings / config
                _progress.Value = 92;
                _status.Text = "Saving configuration...";
                WriteConfig(installDir);
                AppendLog("[OK] Settings saved");

                // 7) finish
                _progress.Value = 100;
                _status.Text = "Install complete.";
                AppendLog("[OK] Install finished successfully.");

                _completeText.Text =
                    "Installation complete!\n\n" +
                    "FNAF Save Manager " + APP_VERSION + " was installed to:\n" + installDir + "\n\n" +
                    "• Desktop shortcut: " + (_chkDesktop.Checked ? "yes" : "no") + "\n" +
                    "• Start Menu shortcut: " + (_chkStartMenu.Checked ? "yes" : "no") + "\n" +
                    "• Automatic backups: " + (_chkAutoBackup.Checked ? "enabled" : "disabled") + "\n" +
                    "• Uninstallable from Windows Apps & Features at any time.";

                ShowPage(Page.Complete);

                if (_chkLaunch.Checked)
                {
                    try { Process.Start(dstExe); } catch { }
                }
                if (_chkUpdateCheck.Checked) CheckForUpdates(installDir);
                _btnInstall.Enabled = true;
                _btnInstall.Text = "Finish";
            }
            catch (Exception ex)
            {
                AppendLog("[ERROR] " + ex.Message);
                Rollback(installDir, dstCopied);
                if (_logPath != null) AppendLog("[INFO] A copy of the install log was saved to " + _logPath);
                _status.Text = "Install failed.";
                MessageBox.Show(this, "Install error: " + ex.Message + "\n\nIf the app is currently running, close it and try again.\n\nA log file was saved to:\n" + _logPath,
                    "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                _btnInstall.Enabled = true;
            }
        }

        private void CheckForUpdates(string installDir)
        {
            try
            {
                AppendLog("[INFO] Checking for updates...");
                if (string.IsNullOrEmpty(UPDATE_URL))
                {
                    AppendLog("[INFO] No update server configured.");
                    return;
                }
                string latest = null;
                using (WebClient wc = new WebClient())
                {
                    wc.Headers.Add("User-Agent", "FNAF-Save-Manager/" + APP_VERSION);
                    latest = wc.DownloadString(UPDATE_URL).Trim();
                }
                string remote = latest.StartsWith("v", StringComparison.OrdinalIgnoreCase) ? latest : "v" + latest;
                if (string.Compare(remote, APP_VERSION) > 0)
                {
                    AppendLog("[UPDATE] A newer version is available: " + remote);
                    MessageBox.Show(this, "A newer version of " + APP_NAME + " is available: " + remote +
                        "\n\nYou can download it from the official page.", "Update Available",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                else
                {
                    AppendLog("[OK] " + APP_NAME + " is up to date (" + APP_VERSION + ").");
                }
            }
            catch (Exception ex)
            {
                AppendLog("[WARN] Update check failed: " + ex.Message);
            }
        }

        private void Rollback(string installDir, bool dstCopied)
        {
            try
            {
                AppendLog("[ROLLBACK] Undoing partial install...");
                string dstExe = Path.Combine(installDir, APP_EXE);
                if (dstCopied && File.Exists(dstExe)) File.Delete(dstExe);
                try { Registry.CurrentUser.DeleteSubKeyTree(UNINSTALL_KEY, false); } catch { }
                try
                {
                    File.Delete(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), APP_NAME + ".lnk"));
                }
                catch { }
                try
                {
                    File.Delete(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Microsoft", "Windows", "Start Menu", "Programs", APP_NAME + ".lnk"));
                }
                catch { }
                try { File.Delete(Path.Combine(installDir, "fsm_config.ini")); } catch { }
                AppendLog("[ROLLBACK] Completed.");
            }
            catch (Exception ex)
            {
                AppendLog("[WARN] Rollback error: " + ex.Message);
            }
        }

        private void CopyResourceWithProgress(string resourceName, string dst, int startPct, int endPct)
        {
            using (Stream res = Assembly.GetExecutingAssembly().GetManifestResourceStream(resourceName))
            {
                if (res == null) throw new IOException("Embedded resource not found: " + resourceName);
                using (FileStream outFs = new FileStream(dst, FileMode.Create, FileAccess.Write))
                {
                    byte[] buf = new byte[256 * 1024];
                    long total = res.Length;
                    long done = 0;
                    int read;
                    while ((read = res.Read(buf, 0, buf.Length)) > 0)
                    {
                        outFs.Write(buf, 0, read);
                        done += read;
                        int pct = startPct + (int)((long)(endPct - startPct) * done / Math.Max(total, 1));
                        _progress.Value = Math.Min(99, pct);
                        Application.DoEvents();
                    }
                    outFs.Flush();
                }
            }
        }

        private void AppendLog(string msg)
        {
            _log.AppendText(msg + "\n");
            _log.SelectionStart = _log.TextLength;
            _log.ScrollToCaret();
            if (_logPath != null)
            {
                try { File.AppendAllText(_logPath, DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss ") + msg + "\n"); } catch { }
            }
            Application.DoEvents();
        }

        private void WriteRegistry(string installDir, string dstExe)
        {
            using (RegistryKey key = Registry.CurrentUser.CreateSubKey(UNINSTALL_KEY))
            {
                key.SetValue("DisplayName", APP_NAME);
                key.SetValue("DisplayVersion", APP_VERSION);
                key.SetValue("DisplayIcon", dstExe + ",0");
                key.SetValue("Publisher", PUBLISHER);
                key.SetValue("InstallLocation", installDir);
                key.SetValue("UninstallString", "\"" + Application.ExecutablePath + "\" --uninstall --path=\"" + installDir + "\"");
                key.SetValue("NoModify", 1);
                key.SetValue("NoRepair", 1);
                key.SetValue("EstimatedSize", Math.Max(1, _appSizeBytes / 1024));
            }
        }

        private void WriteConfig(string installDir)
        {
            StringBuilder sb = new StringBuilder();
            sb.AppendLine("; FNAF Save Manager - install-time configuration");
            sb.AppendLine("[options]");
            sb.AppendLine("autobackup=" + (_chkAutoBackup.Checked ? "1" : "0"));
            sb.AppendLine("music=" + (_chkMusic.Checked ? "1" : "0"));
            sb.AppendLine("updatecheck=" + (_chkUpdateCheck.Checked ? "1" : "0"));
            sb.AppendLine("[install]");
            sb.AppendLine("path=" + installDir);
            sb.AppendLine("version=" + APP_VERSION);
            sb.AppendLine("date=" + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
            string cfg = Path.Combine(installDir, "fsm_config.ini");
            File.WriteAllText(cfg, sb.ToString());
        }

        private static Label MkLabel(string text, float size, bool bold)
        {
            Label l = new Label();
            l.Text = text;
            l.Font = new Font("Segoe UI", size, bold ? FontStyle.Bold : FontStyle.Regular);
            return l;
        }

        private void OnShown(object sender, EventArgs e)
        {
            if (_autoInstall)
            {
                // relaunched elevated: jump straight to install
                _pathBox.Focus();
                ShowPage(Page.Install);
                BeginInstall();
            }
            else if (!string.IsNullOrEmpty(_existingInstall) && _page == Page.Welcome)
            {
                // keep welcome text above (already shown) - no blocking dialog
            }
            if (_chkMusic.Checked) PlayMusic();
        }

        private void OnClosed(object sender, FormClosedEventArgs e)
        {
            StopMusic();
        }

        private void PlayMusic()
        {
            try
            {
                byte[] bytes = ReadResource("InstallerMusic");
                if (bytes == null) return;
                _musicPath = Path.Combine(Path.GetTempPath(), "fsm_install_music.mp3");
                File.WriteAllBytes(_musicPath, bytes);
                mciSendString("close " + MUSIC_ALIAS, null, 0, IntPtr.Zero);
                mciSendString("open \"" + _musicPath + "\" type mpegvideo alias " + MUSIC_ALIAS, null, 0, IntPtr.Zero);
                mciSendString("play " + MUSIC_ALIAS + " repeat", null, 0, IntPtr.Zero);
            }
            catch { }
        }

        private void StopMusic()
        {
            try
            {
                mciSendString("stop " + MUSIC_ALIAS, null, 0, IntPtr.Zero);
                mciSendString("close " + MUSIC_ALIAS, null, 0, IntPtr.Zero);
            }
            catch { }
            if (_musicPath != null) { try { File.Delete(_musicPath); } catch { } }
        }

        // ------------------------------------------------------------------ //
        //  helpers                                                             //
        // ------------------------------------------------------------------ //
        private static string LicenseText()
        {
            return
                "FNAF Save Manager - End User License Agreement (EULA)\r\n" +
                "\r\n" +
                "Version " + APP_VERSION + "  |  Created by " + PUBLISHER + "\r\n" +
                "\r\n" +
                "1. GRANT OF LICENSE\r\n" +
                "FNAF Save Manager is provided FREE of charge for personal, non-commercial use.\r\n" +
                "You may install and use the software on any number of computers you own.\r\n" +
                "\r\n" +
                "2. RESTRICTIONS\r\n" +
                "You may NOT sell, redistribute, or modify this software, in whole or in part,\r\n" +
                "without written permission from the author.\r\n" +
                "\r\n" +
                "3. SAVE DATA\r\n" +
                "The software edits save files of Five Nights at Freddy's games. Always create\r\n" +
                "backups. The author is not responsible for corrupted or lost game saves.\r\n" +
                "\r\n" +
                "4. DISCLAIMER OF WARRANTY\r\n" +
                "This software is provided \"as is\", without warranty of any kind, express or\r\n" +
                "implied, including but not limited to the warranties of merchantability,\r\n" +
                "fitness for a particular purpose, or noninfringement.\r\n" +
                "\r\n" +
                "5. LIMITATION OF LIABILITY\r\n" +
                "In no event shall the author be liable for any damages arising from the use of\r\n" +
                "this software.\r\n" +
                "\r\n" +
                "6. Five Nights at Freddy's is a trademark of Scott Cawthon. FNAF Save Manager\r\n" +
                "is an unofficial fan-made tool and is not affiliated with or endorsed by the\r\n" +
                "trademark owner.\r\n" +
                "\r\n" +
                "By clicking Next you accept the terms of this agreement. If you do not agree,\r\n" +
                "click Cancel to exit the installer.";
        }

        private string FindExistingInstall()
        {
            string[] dirs = new string[]
            {
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", APP_NAME),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), APP_NAME),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), APP_NAME),
            };
            foreach (string dir in dirs)
            {
                try { if (File.Exists(Path.Combine(dir, APP_EXE))) return dir; } catch { }
            }
            // shortcut-based detection
            string[] links = new string[]
            {
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), APP_NAME + ".lnk"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Microsoft", "Windows", "Start Menu", "Programs", APP_NAME + ".lnk"),
            };
            foreach (string link in links)
            {
                try { if (File.Exists(link)) return "via shortcut"; } catch { }
            }
            return null;
        }

        private void CreateShortcut(string folder, string target, string workDir)
        {
            if (string.IsNullOrEmpty(folder)) return;
            try { Directory.CreateDirectory(folder); } catch { }
            string link = Path.Combine(folder, APP_NAME + ".lnk");
            try
            {
                dynamic shell = Activator.CreateInstance(Type.GetTypeFromProgID("WScript.Shell"));
                dynamic sc = shell.CreateShortcut(link);
                sc.TargetPath = target;
                sc.WorkingDirectory = workDir;
                sc.Description = APP_NAME + " " + APP_VERSION;
                sc.Save();
            }
            catch { }
        }
    }
}