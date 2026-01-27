import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/other_providers.dart';
import '../models/models.dart';
import '../widgets/app_drawer.dart';

class UsersScreen extends StatefulWidget {
  const UsersScreen({Key? key}) : super(key: key);

  @override
  State<UsersScreen> createState() => _UsersScreenState();
}

class _UsersScreenState extends State<UsersScreen> {
  late TextEditingController _usernameController;
  late TextEditingController _emailController;
  late TextEditingController _passwordController;
  late TextEditingController _fullNameController;
  String _selectedRole = 'user';

  @override
  void initState() {
    super.initState();
    _usernameController = TextEditingController();
    _emailController = TextEditingController();
    _passwordController = TextEditingController();
    _fullNameController = TextEditingController();
    // Fetch users on initial load
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<UserProvider>(context, listen: false).fetchUsers();
    });
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _fullNameController.dispose();
    super.dispose();
  }

  void _showCreateDialog() {
    _usernameController.clear();
    _emailController.clear();
    _passwordController.clear();
    _fullNameController.clear();
    _selectedRole = 'user';

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('Create User'),
          content: SingleChildScrollView(
            child: SizedBox(
              width: 400,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: _usernameController,
                    decoration: const InputDecoration(
                      labelText: 'Username',
                      hintText: 'Enter username',
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _emailController,
                    decoration: const InputDecoration(
                      labelText: 'Email',
                      hintText: 'user@example.com',
                    ),
                    keyboardType: TextInputType.emailAddress,
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _passwordController,
                    decoration: const InputDecoration(
                      labelText: 'Password',
                      hintText: 'At least 8 characters',
                    ),
                    obscureText: true,
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _fullNameController,
                    decoration: const InputDecoration(
                      labelText: 'Full Name (Optional)',
                      hintText: 'Enter full name',
                    ),
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    value: _selectedRole,
                    decoration: const InputDecoration(labelText: 'Role'),
                    items: const [
                      DropdownMenuItem(value: 'user', child: Text('User')),
                      DropdownMenuItem(value: 'admin', child: Text('Admin')),
                    ],
                    onChanged: (value) {
                      setState(() => _selectedRole = value!);
                    },
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                if (_usernameController.text.isEmpty ||
                    _emailController.text.isEmpty ||
                    _passwordController.text.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text(
                        'Username, email and password are required',
                      ),
                    ),
                  );
                  return;
                }

                final userProvider = Provider.of<UserProvider>(
                  context,
                  listen: false,
                );
                final success = await userProvider.createUser(
                  username: _usernameController.text,
                  email: _emailController.text,
                  password: _passwordController.text,
                  role: _selectedRole,
                  fullName: _fullNameController.text.isNotEmpty
                      ? _fullNameController.text
                      : null,
                );

                if (success && mounted) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('User created successfully')),
                  );
                } else if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                        userProvider.error ?? 'Failed to create user',
                      ),
                    ),
                  );
                }
              },
              child: const Text('Create'),
            ),
          ],
        ),
      ),
    );
  }

  void _showEditDialog(User user) {
    _usernameController.text = user.username;
    _emailController.text = user.email;
    _fullNameController.text = user.fullName ?? '';
    _selectedRole = user.role;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('Edit User'),
          content: SingleChildScrollView(
            child: SizedBox(
              width: 400,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: _usernameController,
                    decoration: const InputDecoration(labelText: 'Username'),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _emailController,
                    decoration: const InputDecoration(labelText: 'Email'),
                    keyboardType: TextInputType.emailAddress,
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _fullNameController,
                    decoration: const InputDecoration(labelText: 'Full Name'),
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    value: _selectedRole,
                    decoration: const InputDecoration(labelText: 'Role'),
                    items: const [
                      DropdownMenuItem(value: 'user', child: Text('User')),
                      DropdownMenuItem(value: 'admin', child: Text('Admin')),
                    ],
                    onChanged: (value) {
                      setState(() => _selectedRole = value!);
                    },
                  ),
                  const SizedBox(height: 16),
                  SwitchListTile(
                    title: const Text('Active'),
                    value: user.isActive,
                    onChanged: (value) {
                      setState(() {});
                    },
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final userProvider = Provider.of<UserProvider>(
                  context,
                  listen: false,
                );
                final success = await userProvider.updateUser(
                  user.id,
                  username: _usernameController.text,
                  email: _emailController.text,
                  role: _selectedRole,
                  fullName: _fullNameController.text.isNotEmpty
                      ? _fullNameController.text
                      : null,
                  isActive: user.isActive,
                );

                if (success && mounted) {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('User updated successfully')),
                  );
                } else if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                        userProvider.error ?? 'Failed to update user',
                      ),
                    ),
                  );
                }
              },
              child: const Text('Update'),
            ),
          ],
        ),
      ),
    );
  }

  void _confirmDelete(User user) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete User'),
        content: Text(
          'Are you sure you want to delete user "${user.username}"? This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              final userProvider = Provider.of<UserProvider>(
                context,
                listen: false,
              );
              final success = await userProvider.deleteUser(user.id);

              if (success && mounted) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('User deleted successfully')),
                );
              } else if (mounted) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      userProvider.error ?? 'Failed to delete user',
                    ),
                  ),
                );
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    final userProvider = Provider.of<UserProvider>(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('User Management'),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => userProvider.fetchUsers(),
            tooltip: 'Refresh',
          ),
        ],
      ),
      drawer: const AppDrawer(),
      floatingActionButton: authProvider.isAdmin
          ? FloatingActionButton(
              onPressed: _showCreateDialog,
              child: const Icon(Icons.add),
              tooltip: 'Create User',
            )
          : null,
      body: userProvider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : userProvider.error != null
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 64, color: Colors.red),
                  const SizedBox(height: 16),
                  Text(
                    'Error: ${userProvider.error}',
                    style: const TextStyle(color: Colors.red),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => userProvider.fetchUsers(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            )
          : userProvider.users.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.people_outline,
                    size: 64,
                    color: Colors.grey,
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'No users found',
                    style: TextStyle(fontSize: 16, color: Colors.grey),
                  ),
                  if (authProvider.isAdmin) ...[
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: _showCreateDialog,
                      icon: const Icon(Icons.add),
                      label: const Text('Create User'),
                    ),
                  ],
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: userProvider.users.length,
              itemBuilder: (context, index) {
                final user = userProvider.users[index];
                return Card(
                  color: user.isActive ? null : Colors.grey[200],
                  child: ListTile(
                    leading: Icon(
                      user.isAdmin ? Icons.admin_panel_settings : Icons.person,
                      color: user.isActive
                          ? (user.isAdmin ? Colors.purple : Colors.blue)
                          : Colors.grey,
                    ),
                    title: Text(
                      user.username,
                      style: TextStyle(
                        color: user.isActive ? null : Colors.grey[600],
                        decoration: user.isActive
                            ? null
                            : TextDecoration.lineThrough,
                      ),
                    ),
                    subtitle: Text(
                      '${user.email} • ${user.role.toUpperCase()}${user.isActive ? '' : ' (Inactive)'}',
                      style: TextStyle(
                        color: user.isActive ? null : Colors.grey[600],
                      ),
                    ),
                    trailing: authProvider.isAdmin
                        ? PopupMenuButton(
                            itemBuilder: (context) => [
                              PopupMenuItem(
                                child: const Text('Edit'),
                                onTap: () => _showEditDialog(user),
                              ),
                              PopupMenuItem(
                                child: Text(
                                  user.isActive ? 'Deactivate' : 'Activate',
                                ),
                                onTap: () => userProvider.updateUser(
                                  user.id,
                                  username: user.username,
                                  email: user.email,
                                  role: user.role,
                                  fullName: user.fullName,
                                  isActive: !user.isActive,
                                ),
                              ),
                              PopupMenuItem(
                                child: const Text('Delete'),
                                onTap: () => _confirmDelete(user),
                              ),
                            ],
                          )
                        : null,
                  ),
                );
              },
            ),
    );
  }
}
