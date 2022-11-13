package discoverdataset;

import org.eclipse.equinox.app.IApplication;
import org.eclipse.equinox.app.IApplicationContext;
import org.eclipse.jdt.core.IJavaProject;
import org.eclipse.jdt.core.JavaCore;
import org.eclipse.modisco.java.discoverer.DiscoverJavaModelFromJavaProject;
import org.eclipse.modisco.java.discoverer.JavaDiscoveryConstants;

import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

import org.eclipse.core.resources.IProject;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.resources.IWorkspaceRoot;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.NullProgressMonitor;
import org.eclipse.emf.ecore.resource.Resource;
import org.eclipse.emf.ecore.xmi.XMLResource;

public class Application implements IApplication {

	@Override
	public Object start(IApplicationContext context) throws Exception {
		System.out.println("starting plugin...");
		
		discoverDataset();
		
		/*Path srcPath = Paths.get("C:\\Users\\Nic\\runtime-test-withhead\\TheTargetProject\\src\\thePackage\\TheClass.java");
		String content = Files.readString(srcPath);
		System.out.println("content: " + content);
		
		content = content.replace("yes...", "no...");
		Files.writeString(srcPath, content);
		
		go("a2");*/

		System.out.println("end...");
		return null;
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
			
			System.out.println("found project " + project.getName());
			
			String projectFolder = project.getProject().getFullPath().toString();
			
			Path targetClassPath = Paths.get(workspaceFolder, projectFolder, "src", "targetpackage", "TargetClass.java");
			String contents = Files.readString(targetClassPath);
			System.out.println("contents: " + contents);
			
			project.refreshLocal(IResource.DEPTH_INFINITE, null);
			IJavaProject javaProject = JavaCore.create(project);

			long start = System.currentTimeMillis();
			
			JavaProjectDiscoverer projectDiscoverer = new JavaProjectDiscoverer();
			String xmi = projectDiscoverer.discover(javaProject);
			
			Path dstPath = Paths.get(workspaceFolder, projectFolder, "out.xmi");
			Files.writeString(dstPath, xmi);
			
			long finish = System.currentTimeMillis();
			long timeElapsed = finish - start;
			System.out.println("elapsed: " + timeElapsed);
		}
	}

	@Override
	public void stop() {
		System.out.println("stopping plugin...");
	}

}

class JavaProjectDiscoverer extends DiscoverJavaModelFromJavaProject {
	public String discover(IJavaProject project) throws Exception {
		System.out.println("discovering java project...");
		
		basicDiscoverElement(project, new NullProgressMonitor());
		
		System.out.println("retrieving xmi...");

		Resource targetModel = getTargetModel();
		ByteArrayOutputStream stream = new ByteArrayOutputStream();
		
		Map<String, Object> options = new HashMap<String, Object>();
		options.put(XMLResource.OPTION_FLUSH_THRESHOLD, 65536);
		options.put(XMLResource.OPTION_USE_FILE_BUFFER, Boolean.TRUE);
		
		targetModel.save(stream, options);
		String xmi = new String(stream.toByteArray());
		
		return xmi;
	}
}
