import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

class AppDrawer extends StatelessWidget {
  const AppDrawer({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: BoxDecoration(color: Theme.of(context).primaryColor),
            child: Consumer<AuthProvider>(
              builder: (context, auth, _) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    const Text(
                      'Reverse Proxy MCP',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Logged in as ${auth.currentUser?.email ?? "Unknown"}',
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 12,
                      ),
                    ),
                    if (auth.currentUser?.role == 'admin')
                      const Text(
                        'Administrator',
                        style: TextStyle(
                          color: Colors.yellow,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                  ],
                );
              },
            ),
          ),
          ListTile(
            leading: const Icon(Icons.dashboard),
            title: const Text('Dashboard'),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/dashboard');
            },
          ),
          ListTile(
            leading: const Icon(Icons.storage),
            title: const Text('Backend Servers'),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/backends');
            },
          ),
          ListTile(
            leading: const Icon(Icons.domain),
            title: const Text('Proxy Rules'),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/rules');
            },
          ),
          ListTile(
            leading: const Icon(Icons.security),
            title: const Text('SSL Certificates'),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/certificates');
            },
          ),
          Consumer<AuthProvider>(
            builder: (context, auth, _) {
              if (auth.currentUser?.role == 'admin') {
                return Column(
                  children: [
                    const Divider(),
                    ListTile(
                      leading: const Icon(Icons.people),
                      title: const Text('Users'),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/users');
                      },
                    ),
                    ListTile(
                      leading: const Icon(Icons.history),
                      title: const Text('Audit Logs'),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/audit');
                      },
                    ),
                  ],
                );
              }
              return const SizedBox.shrink();
            },
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Logout'),
            onTap: () async {
              Navigator.pop(context);
              await context.read<AuthProvider>().logout();
              if (context.mounted) {
                Navigator.pushReplacementNamed(context, '/login');
              }
            },
          ),
        ],
      ),
    );
  }
}
