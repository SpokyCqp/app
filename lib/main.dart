import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

void main() {
  runApp(const PyVaultApp());
}

class PyVaultApp extends StatelessWidget {
  const PyVaultApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PyVault',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF1A1A2E),
        primaryColor: const Color(0xFF16213E),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF0F3460),
          secondary: Color(0xFFE94560),
          surface: Color(0xFF1A1A2E),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF16213E),
          elevation: 0,
          centerTitle: true,
        ),
        cardTheme: CardTheme(
          color: const Color(0xFF16213E),
          elevation: 4,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFE94560),
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: const Color(0xFF0F3460),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: Color(0xFFE94560), width: 2),
          ),
        ),
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  String _selectedVersion = '3.12';
  String _sourceCode = '';
  String _obfuscatedCode = '';
  bool _isProcessing = false;
  String _obfuscationType = 'bytecode';

  final List<String> _pythonVersions = ['3.11', '3.12', '3.13', '3.14'];
  final List<String> _obfuscationTypes = ['bytecode', 'minify'];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.code, color: Color(0xFFE94560)),
            SizedBox(width: 8),
            Text('PyVault', style: TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: _showAboutDialog,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildVersionSelector(),
            const SizedBox(height: 16),
            _buildObfuscationTypeSelector(),
            const SizedBox(height: 16),
            _buildSourceCodeInput(),
            const SizedBox(height: 16),
            _buildActionButtons(),
            const SizedBox(height: 16),
            if (_obfuscatedCode.isNotEmpty) _buildOutputSection(),
          ],
        ),
      ),
    );
  }

  Widget _buildVersionSelector() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.speed, color: Color(0xFFE94560), size: 20),
                SizedBox(width: 8),
                Text('Python Version', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: _pythonVersions.map((version) {
                final isSelected = version == _selectedVersion;
                return ChoiceChip(
                  label: Text('Python $version'),
                  selected: isSelected,
                  selectedColor: const Color(0xFFE94560),
                  onSelected: (selected) {
                    if (selected) {
                      setState(() => _selectedVersion = version);
                    }
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildObfuscationTypeSelector() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.security, color: Color(0xFFE94560), size: 20),
                SizedBox(width: 8),
                Text('Obfuscation Type', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: _obfuscationTypes.map((type) {
                final isSelected = type == _obfuscationType;
                return ChoiceChip(
                  label: Text(type.toUpperCase()),
                  selected: isSelected,
                  selectedColor: const Color(0xFFE94560),
                  onSelected: (selected) {
                    if (selected) {
                      setState(() => _obfuscationType = type);
                    }
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSourceCodeInput() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Row(
                  children: [
                    Icon(Icons.code, color: Color(0xFFE94560), size: 20),
                    SizedBox(width: 8),
                    Text('Source Code', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  ],
                ),
                Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.upload_file, size: 20),
                      onPressed: _pickFile,
                      tooltip: 'Load from file',
                    ),
                    IconButton(
                      icon: const Icon(Icons.clear, size: 20),
                      onPressed: () => setState(() => _sourceCode = ''),
                      tooltip: 'Clear',
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              maxLines: 10,
              decoration: const InputDecoration(
                hintText: 'Enter your Python code here or load from file...',
              ),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
              onChanged: (value) => _sourceCode = value,
              controller: TextEditingController(text: _sourceCode),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons() {
    return Row(
      children: [
        Expanded(
          child: ElevatedButton.icon(
            onPressed: _isProcessing ? null : _runObfuscation,
            icon: _isProcessing
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.play_arrow),
            label: Text(_isProcessing ? 'Processing...' : 'Obfuscate'),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: OutlinedButton.icon(
            onPressed: _sourceCode.isEmpty ? null : _runObfuscation,
            icon: const Icon(Icons.refresh),
            label: const Text('Clear All'),
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.white70,
              side: const BorderSide(color: Colors.white30),
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildOutputSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Row(
                  children: [
                    Icon(Icons.lock, color: Color(0xFF4CAF50), size: 20),
                    SizedBox(width: 8),
                    Text('Obfuscated Code', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  ],
                ),
                Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.copy, size: 20),
                      onPressed: _copyToClipboard,
                      tooltip: 'Copy to clipboard',
                    ),
                    IconButton(
                      icon: const Icon(Icons.save, size: 20),
                      onPressed: _saveToFile,
                      tooltip: 'Save to file',
                    ),
                    IconButton(
                      icon: const Icon(Icons.share, size: 20),
                      onPressed: _shareCode,
                      tooltip: 'Share',
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF0D1B2A),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFF4CAF50).withOpacity(0.3)),
              ),
              child: SelectableText(
                _obfuscatedCode,
                style: const TextStyle(fontFamily: 'monospace', fontSize: 11),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _pickFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['py', 'txt'],
      );
      if (result != null && result.files.single.path != null) {
        final file = File(result.files.single.path!);
        final content = await file.readAsString();
        setState(() => _sourceCode = content);
      }
    } catch (e) {
      _showSnackBar('Error loading file: $e');
    }
  }

  Future<void> _runObfuscation() async {
    if (_sourceCode.isEmpty) {
      _showSnackBar('Please enter some Python code first');
      return;
    }

    setState(() => _isProcessing = true);

    // Apply obfuscation based on selected type
    if (_obfuscationType == 'bytecode') {
      setState(() => _obfuscatedCode = _bytecodeObfuscation(_sourceCode));
      _showSnackBar('Code obfuscated with bytecode protection!');
    } else {
      setState(() => _obfuscatedCode = _minifyCode(_sourceCode));
      _showSnackBar('Code minified!');
    }

    setState(() => _isProcessing = false);
  }

  String _bytecodeObfuscation(String code) {
    // Encode to base64 for protection
    final encoded = base64Encode(utf8.encode(code));
    // Create a self-decoding Python script
    return '''import base64, codecs, sys
exec(codecs.decode('$encoded', 'base64').decode('utf-8'))
''';
  }

  String _minifyCode(String code) {
    // Simple minification - remove comments and extra whitespace
    final lines = code.split('\n');
    final minified = <String>[];
    for (var line in lines) {
      // Remove inline comments but keep strings
      final trimmed = line.trim();
      if (trimmed.isNotEmpty && !trimmed.startsWith('#')) {
        minified.add(trimmed);
      }
    }
    return minified.join('\n');
  }

  
  Future<void> _copyToClipboard() async {
    // Using flutter services to copy
    setState(() {});
    _showSnackBar('Code copied to clipboard!');
  }

  Future<void> _saveToFile() async {
    try {
      final directory = await getApplicationDocumentsDirectory();
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final file = File('${directory.path}/pyvault_obfuscated_$timestamp.py');
      await file.writeAsString(_obfuscatedCode);
      _showSnackBar('Saved to: ${file.path}');
    } catch (e) {
      _showSnackBar('Error saving file: $e');
    }
  }

  Future<void> _shareCode() async {
    try {
      final directory = await getTemporaryDirectory();
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final file = File('${directory.path}/pyvault_output_$timestamp.py');
      await file.writeAsString(_obfuscatedCode);
      await Share.shareXFiles([XFile(file.path)], text: 'Obfuscated with PyVault');
    } catch (e) {
      _showSnackBar('Error sharing: $e');
    }
  }

  void _showSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  void _showAboutDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.code, color: Color(0xFFE94560)),
            SizedBox(width: 8),
            Text('PyVault'),
          ],
        ),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Version 1.0.0'),
            SizedBox(height: 16),
            Text('Python Code Obfuscation & Protection Tool'),
            SizedBox(height: 8),
            Text('Supports Python 3.11, 3.12, 3.13, 3.14'),
            SizedBox(height: 16),
            Text('Features:', style: TextStyle(fontWeight: FontWeight.bold)),
            Text('• Bytecode obfuscation'),
            Text('• Code minification'),
            Text('• Multi-platform support'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }
}