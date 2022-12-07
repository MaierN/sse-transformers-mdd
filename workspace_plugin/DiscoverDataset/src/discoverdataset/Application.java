package discoverdataset;

import org.eclipse.equinox.app.IApplication;
import org.eclipse.equinox.app.IApplicationContext;
import org.eclipse.jdt.core.IJavaProject;
import org.eclipse.jdt.core.JavaCore;
import org.eclipse.modisco.infra.discovery.core.exception.DiscoveryException;
import org.eclipse.modisco.java.discoverer.DiscoverJavaModelFromJavaProject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.IWorkspaceRoot;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.NullProgressMonitor;
import org.eclipse.emf.ecore.resource.Resource;
import org.eclipse.emf.ecore.xmi.XMLResource;

import org.json.JSONObject;

public class Application implements IApplication {

	@Override
	public Object start(IApplicationContext context) throws Exception {
		System.out.println("starting plugin...");
		
		//discoverDataset();
		testDiscovery();
		ResourcesPlugin.getWorkspace().save(true, null);

		return 0;
	}

	@Override
	public void stop() {
		System.out.println("stopping plugin...");
	}
	
	private void testDiscovery() throws Exception {
		System.out.println("testing...");
		
		IWorkspaceRoot workspaceRoot = ResourcesPlugin.getWorkspace().getRoot();
		IProject[] projects = workspaceRoot.getProjects();
		
		String workspaceFolder = workspaceRoot.getLocation().toOSString();
		
		System.out.println("workspace " + workspaceFolder);
		
		for (IProject project : projects) {
			if (!project.getName().equals("TargetProject")) {
				continue;
			}
			
			System.out.println("project " + project.getName());
			
			String projectFolder = project.getProject().getFullPath().toString();
			
			Path targetClassPath1 = Paths.get(workspaceFolder, projectFolder, "src", "targetpackage", "TargetClass1.java");
			Path targetClassPath2 = Paths.get(workspaceFolder, projectFolder, "src", "targetpackage", "TargetClass2.java");
			
			
			List<Path> files = Files.list(Paths.get(workspaceFolder, "..", "dataset", "codesearchnet-java-decompressed")).collect(Collectors.toList());
			for (Path path : files) {
				System.out.println("dataset file " + path);
				
				Path outPath = Paths.get(workspaceFolder, "..", "sequence-dataset", "codesearchnet-java-discovered", path.getFileName().toString());
				Files.writeString(outPath, "");
				
				List<String> lines = Files.readAllLines(path);
				System.out.println("processing " + lines.size() + " lines...");

				long start = System.currentTimeMillis();
				
				int idx = 0;
				for (String line : lines) {
					try {
						JSONObject obj = new JSONObject(line);
						
						String contents1 = "package targetpackage;\n"
								+ "\n"
								+ "public class TargetClass1 {\n"
								+ "    public static void main(String[] args) {\n"
								+ "        System.out.println(\"aaabbb\");"
								+ "    }"
								+ "}\n";
						Files.writeString(targetClassPath1, contents1);
						
						String contents2 = "package targetpackage;\n"
								+ "\n"
								+ "public class TargetClass2 {\n"
								+ "    public void testFunc() {\n"
								+ "        System.out.println(\"ccccdddd\");"
								+ "    }"
								+ "}\n";
						Files.writeString(targetClassPath2, contents2);
						
						project.refreshLocal(IResource.DEPTH_INFINITE, null);
						IJavaProject javaProject = JavaCore.create(project);
						
						JavaProjectDiscoverer projectDiscoverer = new JavaProjectDiscoverer();
						String xmi = projectDiscoverer.discover(javaProject);
						
						if (xmi != null) {
							JSONObject res = new JSONObject();
							res.put("originalLine", idx);
							res.put("code", obj.get("code"));
							res.put("contents1", contents1);
							res.put("contents2", contents2);
							res.put("xmi", xmi);
							
							Files.writeString(outPath, res.toString() + "\n", StandardOpenOption.APPEND);
						}
					} catch (Exception e) {
						System.out.println("error while processing line " + idx + ": " + e.getMessage());
						e.printStackTrace();
					}
					
					idx += 1;
					if (idx % 1000 == 0) {
						System.out.println(idx + " / " + lines.size());
						long curr = System.currentTimeMillis();
						long timeElapsed = curr - start;
						System.out.println("  -> elapsed: " + timeElapsed);
					}
					
					break;
				}

				long finish = System.currentTimeMillis();
				long timeElapsed = finish - start;
				System.out.println("elapsed: " + timeElapsed);
				
				break;
			}
		}
	}
	
	private void discoverDataset() throws Exception {
		IWorkspaceRoot workspaceRoot = ResourcesPlugin.getWorkspace().getRoot();
		IProject[] projects = workspaceRoot.getProjects();
		
		String workspaceFolder = workspaceRoot.getLocation().toOSString();
		
		System.out.println("workspace " + workspaceFolder);
		
		for (IProject project : projects) {
			if (!project.getName().equals("TargetProject")) {
				continue;
			}
			
			System.out.println("project " + project.getName());
			
			String projectFolder = project.getProject().getFullPath().toString();
			
			Path targetClassPath = Paths.get(workspaceFolder, projectFolder, "src", "targetpackage", "TargetClass.java");
			
			
			List<Path> files = Files.list(Paths.get(workspaceFolder, "..", "dataset", "codesearchnet-java-decompressed")).collect(Collectors.toList());
			for (Path path : files) {
				System.out.println("dataset file " + path);
				
				Path outPath = Paths.get(workspaceFolder, "..", "dataset", "codesearchnet-java-discovered", path.getFileName().toString());
				Files.writeString(outPath, "");
				
				List<String> lines = Files.readAllLines(path);
				System.out.println("processing " + lines.size() + " lines...");

				long start = System.currentTimeMillis();
				
				int idx = 0;
				for (String line : lines) {
					try {
						JSONObject obj = new JSONObject(line);
						
						String contents = "package targetpackage;\n"
								+ "\n"
								+ "public class TargetClass {\n"
								+ "    " + obj.getString("code") + "\n"
								+ "}\n";
						Files.writeString(targetClassPath, contents);
						
						project.refreshLocal(IResource.DEPTH_INFINITE, null);
						IJavaProject javaProject = JavaCore.create(project);
						
						JavaProjectDiscoverer projectDiscoverer = new JavaProjectDiscoverer();
						String xmi = projectDiscoverer.discover(javaProject);
						
						if (xmi != null) {
							JSONObject res = new JSONObject();
							res.put("originalLine", idx);
							res.put("code", obj.get("code"));
							res.put("contents", contents);
							res.put("xmi", xmi);
							
							Files.writeString(outPath, res.toString() + "\n", StandardOpenOption.APPEND);
						}
					} catch (Exception e) {
						System.out.println("error while processing line " + idx + ": " + e.getMessage());
						e.printStackTrace();
					}
					
					idx += 1;
					if (idx % 1000 == 0) {
						System.out.println(idx + " / " + lines.size());
						long curr = System.currentTimeMillis();
						long timeElapsed = curr - start;
						System.out.println("  -> elapsed: " + timeElapsed);
					}
				}

				long finish = System.currentTimeMillis();
				long timeElapsed = finish - start;
				System.out.println("elapsed: " + timeElapsed);
			}
		}
	}
}

class JavaProjectDiscoverer extends DiscoverJavaModelFromJavaProject {
	public String discover(IJavaProject project) {
		try {
			basicDiscoverElement(project, new NullProgressMonitor());
		} catch (DiscoveryException e) {
			System.out.println("error while discovering: " + e.getMessage());
			return null;
		}

		Resource targetModel = getTargetModel();
		ByteArrayOutputStream stream = new ByteArrayOutputStream();
		
		Map<String, Object> options = new HashMap<String, Object>();
		options.put(XMLResource.OPTION_FLUSH_THRESHOLD, 65536);
		options.put(XMLResource.OPTION_USE_FILE_BUFFER, Boolean.TRUE);
		
		try {
			targetModel.save(stream, options);
		} catch (IOException e) {
			System.out.println("error while serializing: " + e.getMessage());
			return null;
		}
		String xmi = new String(stream.toByteArray());
		
		return xmi;
	}
}
