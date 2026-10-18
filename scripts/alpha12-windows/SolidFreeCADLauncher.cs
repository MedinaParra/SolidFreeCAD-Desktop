using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

internal static class SolidFreeCADLauncher
{
    [STAThread]
    private static void Main()
    {
        try
        {
            string root = AppDomain.CurrentDomain.BaseDirectory;
            string exe = Path.Combine(root, "Runtime", "FreeCAD.exe");
            if (!File.Exists(exe))
                exe = Path.Combine(root, "Runtime", "bin", "FreeCAD.exe");
            string script = Path.Combine(root, "Application", "SolidFreeCADStandalone.py");
            string user = Path.Combine(root, "UserData");
            if (!File.Exists(exe) || !File.Exists(script))
                throw new FileNotFoundException("Extraiga el paquete completo antes de iniciar SolidFreeCAD.");
            Directory.CreateDirectory(user);
            var start = new ProcessStartInfo(exe);
            start.UseShellExecute = false;
            start.WorkingDirectory = root;
            start.Arguments = "--user-cfg \"" + Path.Combine(user, "user.cfg") + "\" --system-cfg \"" + Path.Combine(user, "system.cfg") + "\" \"" + script + "\"";
            foreach (string variable in new string[] { "PYTHONHOME", "PYTHONPATH", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH" })
                start.EnvironmentVariables.Remove(variable);
            start.EnvironmentVariables["FREECAD_USER_HOME"] = user;
            start.EnvironmentVariables["FREECAD_USER_DATA"] = user;
            start.EnvironmentVariables["QT_QPA_PLATFORM"] = "windows";
            Process.Start(start);
        }
        catch (Exception error)
        {
            MessageBox.Show(error.Message, "SolidFreeCAD", MessageBoxButtons.OK, MessageBoxIcon.Error);
            Environment.ExitCode = 1;
        }
    }
}
