#!/p/gat/tools/perl/perl5.14/bin/perl

=head1 NAME

gen_map_file.pl - Creates the first cut new map file from old map file for generation of ALPS GC data 

=head1 SYNOPSIS

	"help"			For printing help message 
	"man" 			For printing detailed information
	"debug"			For printing the sequence of commands
	"gc_csv_file"		GC CSV file from design team
	"unit_alps_map_file"	Old mapping file from design unit/cluster to ALPS unit/cluster
	"new_alps_map_file"	Output GC file to be used as ALPS input (YAML/CSV)
	"new_skl_format"	GC CSV file in new SKL format (post ww39 2014)
	"new_kbl_format"	GC CSV file in new KBL format (post ww14 2015)
	"powerdb_format"	GC CSV file in power dB format (post ww37 2015)
	"adder_data"		Adder file provided instead of GC CSV file in power dB format (post ww37 2015)
	"yaml"			Output in YAML format
	"csv" 			Output in CSV format

=cut

use strict;
use warnings;

use Getopt::Long;

use Pod::Usage;
use POSIX;
use FindBin qw($Bin);

use Cwd;
use File::Copy;
#use IPC::System::Simple qw(system capture);

use YAML::XS qw(Dump);

#use lib "$Bin/lib/site_perl/5.8.5";

#use Text::CSV::Slurp;


my $optHelp;
my $optMan;
my $debugMode;

my $optYaml;
my $optCsv;

our $opYaml;
our $opCsv;

our $newSklFmt;
our $newKblFmt;
our $pwrDbFmt;
our $adderData;

our $gcCsvFile;
our $unitAlpsMapFileDefault = "$Bin/unitAlpsMap.csv";
our $unitAlpsMapFile;
our $newAlpsMapFile;

Getopt::Long::GetOptions(
	"help" => \$optHelp,
	"man"  => \$optMan,   	
	"debug" => \$debugMode,
	"gc_csv_file=s" => \$gcCsvFile,
	"unit_alps_map_file=s" => \$unitAlpsMapFile,
	"new_alps_map_file=s" => \$newAlpsMapFile,
	"new_skl_format" => \$newSklFmt,
	"new_kbl_format" => \$newKblFmt,
	"powerdb_format" => \$pwrDbFmt,
	"adder_data" => \$adderData,
	"yaml"	=> \$optYaml,
	"csv"	=> \$optCsv		
) or Pod::Usage::pod2usage("Try $0 --help/--man for more information...");

pod2usage( -verbose => 1 ) if $optHelp;
pod2usage( -verbose => 2 ) if $optMan;

if ($gcCsvFile =~ /^\s*$/) {die "Input GC file from design not specified\n";}
if ($newAlpsMapFile =~ /^\s*$/) {die "O/P GC file for ALPS I/P not specified\n";}
if ($unitAlpsMapFile =~ /^\s*$/) 
{
	$unitAlpsMapFile = $unitAlpsMapFileDefault;
	print "ALPS mapping file for units not specified...\n";
	print "Using the default mapping file $unitAlpsMapFile\n";
} else {
	print "Using user provided ALPS mapping file $unitAlpsMapFile...\n";
}

if ($newSklFmt) {print "Input GC file in new SKL format\n";}
if ($newKblFmt) {print "Input GC file in new KBL format\n";}
if ($pwrDbFmt) {print "Input GC file in power dB format\n";}
if ($adderData) {
	if ($pwrDbFmt) { 
		print "Will assume input GC file as HSD adder file in power dB format\n";
	} else {
		die "HSD adder files support only in power dB format\n";
	}
}

if (($newSklFmt && $newKblFmt) || ($newSklFmt && $pwrDbFmt) || ($newKblFmt && $pwrDbFmt)) {die "Cannot specify multiple GC formats at the same time:$!";}

if ($optYaml && !$optCsv) {print "Output file will be dumped in YAML format\n"; $opYaml = 1; $opCsv = 0;} 
if (!$optYaml && $optCsv) {print "Output file will be dumped in CSV format\n"; $opCsv = 1; $opYaml = 0;} 
if ($optYaml && $optCsv) {die "Only one format YAML/CSV is supported at a time\n"} 
if (!$optYaml && !$optCsv) {print "No output format selected. Default output format is CSV\n"; $opCsv = 1; $opYaml = 0;} 


our %alpsMapHash;
our %gcHash;
our %alpsIpTempHash;
our %alpsIpHash;

read_unit_alps_map_file();
read_gc_csv_file();
create_new_alps_map_file();

sub read_unit_alps_map_file {
	my $fileR = $unitAlpsMapFile;
	my $fileRH;
	open $fileRH, "$fileR" or die "Can't open file $fileR:$!";
	my $count = 1;
	my $line = <$fileRH>;
	my %header;
	my @headers = split/,/,$line;
	my $hCount = 0;
	foreach my $head (@headers)
	{
		$head =~ s/^\s*//;
		$head =~ s/\s*$//;
		$header{$head} = $hCount;
		$hCount++;
	}
	while(<$fileRH>) {
		my $line = $_;
		chomp($line);
		#if ($count == 1) {$count++; next;}
		my @parts = split(/,/, $line);
		my $unitName = $parts[$header{"Unit"}];
		#my $unitName = $parts[0];
		if ($unitName) {
			$unitName =~ s/^\s*//;
			$unitName =~ s/\s*$//;
			#$unitName =~ s/1$//;
		}
		else
		{
			die "Cannot find any unit\n";
		}
		my $partName = $parts[$header{"Partition"}];
                #my $partName = $parts[2];
		if ($partName)
		{
                	$partName =~ s/^\s*//;
	                $partName =~ s/\s*$//;
		}
		else
		{
			die "Cannot find partition for unit $unitName\n";
		}

		my $clustName = $parts[$header{"Cluster"}];
		if ($clustName)
		{
                	$clustName =~ s/^\s*//;
	                $clustName =~ s/\s*$//;
		}
		else
		{
			die "Cannot find cluster for unit $unitName\n";
		}

		my $alpsUnitName;
		if (defined $header{"ALPS Unit Name"})
		{
			$alpsUnitName = $parts[$header{"ALPS Unit Name"}];
		}
		elsif (defined $header{"ALPS Unit"})
		{
			$alpsUnitName = $parts[$header{"ALPS Unit"}];
		}
		else
		{
			die "Cannot find a column for ALPS unit name mapping in the map file\n";
		}
		#my $alpsUnitName = $parts[4];
		if ($alpsUnitName)
		{
			$alpsUnitName =~ s/^\s*//;
			$alpsUnitName =~ s/\s*$//;
		}
		else
		{
			warn "No ALPS unit mapping exists for unit $unitName in partition $partName\n";
		}
		my $alpsCluster = $parts[$header{"ALPS Cluster"}];
		#my $alpsCluster = $parts[5];
		if ($alpsCluster)
		{
			$alpsCluster =~ s/^\s*//;
			$alpsCluster =~ s/\s*$//;
		}
		else
		{
			warn "No ALPS cluster mapping exists for unit $unitName in partition $partName\n";
		}
		if ($alpsCluster && $alpsCluster eq "NOT USED") {$count++; next;}
		my $function = $parts[$header{"Functions"}];
		#my $function = $parts[6];
		if ($function)
		{
			$function =~ s/^\s*//;
			$function =~ s/\s*$//;
		}
		else
		{
			warn "No ALPS cluster mapping function exists for unit $unitName in partition $partName\n";
		}
		$alpsMapHash{"$unitName"}{"ALPS"} = $alpsUnitName;
		$alpsMapHash{"$unitName"}{"CLUSTER"} = $clustName;
		$alpsMapHash{"$unitName"}{"PART"} = $partName;
		$alpsMapHash{"$unitName"}{"ALPSCLUSTER"} = $alpsCluster;
		$alpsMapHash{"$unitName"}{"FUNC"} = $function;	
		$alpsMapHash{"$unitName"}{"LINE"} = $line;
		$count++;
	}	
	close $fileRH;
	return 1;
}

sub read_gc_csv_file {
	my $fileR = $gcCsvFile;
	my $fileRH;
	open $fileRH, "$fileR" or die "Can't open file $fileR:$!";
	my $count = 1;
	my %header;
	while(<$fileRH>) {
		my $line = $_;
		$line =~ s/\r//g;
		chomp($line);
		if ($pwrDbFmt)
		{
			if ($count == 1)
			{
				my $hCount = 0;
				my @headers = split(/,/,$line);
				foreach my $head (@headers)
				{
					$header{$head} = $hCount;
					$hCount++;
				}
				$count++;
				next;
			}
		}
		else
		{
			if ($count == 1) {$count++; next;}
		}
		if ($line =~ /^#/) {next;}
		my @parts = split(/,/, $line);
		if ($pwrDbFmt)
		{
			if ($adderData) {
				my $type = $parts[$header{"type"}];
				if ($type !~ /unit/i) {next;}
			}
			#my $unitName = $parts[$header{"Unit"}];
			my $unitName;
			if (defined $header{"Unit"})
			{
				$unitName = $parts[$header{"Unit"}];
			} elsif (defined $header{"unit"}) {
				$unitName = $parts[$header{"unit"}];
			} else {
				die "Cannot find any unit\n";
			}
			my $cluster;
			my $partition;
			my $isGlue;
			my $isPart;
			my $gc;
			if ($adderData) {
				$cluster = $parts[$header{"mega_cluster"}];
				$gc = $parts[$header{"hw_impact_megacluster_syn_kgates"}];
				$gcHash{"$cluster"}{"$unitName"} = $gc;
			} else {
				$partition = $parts[$header{"partition"}];
				$isGlue = $parts[$header{"is_gluelogic"}];
				$isPart = $parts[$header{"is_partition"}];
				if (defined $header{"GC"}) {
					$gc = $parts[$header{"GC"}];
				} elsif (defined $header{"gc"}) {
					$gc = $parts[$header{"gc"}];
				} else {
					die "SD GC file doesn't have a field for GC\n";
				}
				if ($isGlue == 0 && $isPart == 0)
				{
					#print "Part $partition Unit $unitName\n";
					$gcHash{"$partition"}{"$unitName"} = $gc;
				}
			}
			#my $partition = $parts[$header{"Partition"}];
			#my $isGlue = $parts[$header{"Is_gluelogic"}];
			#my $isPart = $parts[$header{"Is_partition"}];
			#my $gc = $parts[$header{"GC"}];
			#if ($isGlue == 0 && $isPart == 0)
			#{
			#	#print "Part $partition Unit $unitName\n";
			#	$gcHash{"$partition"}{"$unitName"} = $gc;
			#}
			#else
			#{
			#	#print "IsGlue $isGlue IsPart $isPart\n";
			#}
		}
		else
		{
			my $unitName = $parts[0];
			$unitName =~ s/^\s*//;
			$unitName =~ s/\s*$//;
			my $cluster;
			if ($newSklFmt) {
				$cluster = $parts[1];
	                } elsif ($newKblFmt) {
	                	$cluster = $parts[11];
	                } else {
				$cluster = $parts[2];
			}
			$cluster =~ s/^\s*//;
			$cluster =~ s/\s*$//;
			if ($cluster eq "NOT USED") {$count++; next;}
			my $partition;
			if ($newSklFmt) {
				$partition = $parts[2];
	                } elsif ($newKblFmt) {
	                	$partition = $parts[10];
			} else {
				$partition = $parts[3];
			}
			$partition =~ s/^\s*//;
			$partition =~ s/\s*$//;
			my $gc;
			if ($newSklFmt) {
				$gc = $parts[6];
	                } elsif ($newKblFmt) {
	                	$gc = $parts[1];
			} else {
				$gc = $parts[10];
			}
			$gc =~ s/^\s*//;
			$gc =~ s/\s*$//;
			#$gc = $gc*1000;
			if ($gc ne "#N/A") {$gc = $gc*1000;}
			#$gcHash{"$unitName"}{"GC"} = $gc;	
			#$gcHash{"$unitName"}{"CLUSTER"} = $cluster;	
			#$gcHash{"$unitName"}{"PARTITION"} = $partition;
			$gcHash{"$cluster"}{"$partition"}{"$unitName"} = $gc;
		}
		$count++;
	}
	close $fileRH;
	return 1;
}

sub create_new_alps_map_file {
	my $fileW = $newAlpsMapFile;
	my $fileWH;
	open $fileWH, ">$fileW" or die "Can't open file $fileW:$!";
	print $fileWH "Unit,Cluster,Partition,ALPS Map,ALPS Unit Name,ALPS Cluster, Functions\n";
	if ($pwrDbFmt)
	{
		if ($adderData) {
			foreach my $cluster (keys %gcHash) {
				my %unitHash = %{$gcHash{"$cluster"}};
				foreach my $unit (keys %unitHash) {
					my $unit1 = $unit."1";
					my $unit0 = $unit."0";
					if (exists $alpsMapHash{"$unit"}) {
	 		              		my $clust = $alpsMapHash{"$unit"}{"CLUSTER"};
				               	if ($cluster eq $clust)
			        	       	{
							my $line = $alpsMapHash{"$unit"}{"LINE"};
							print $fileWH "$line\n";
	                       			}
		                       		else
		                       		{
							my $line = $alpsMapHash{"$unit"}{"LINE"};
							$line =~ s/$clust/$cluster/;
							print $fileWH "$line\n";
							#print $fileWH "$unit,,$partition\n";
		        	       		}
					} elsif (exists $alpsMapHash{"$unit1"}) {
						my $clust = $alpsMapHash{"$unit1"}{"CLUSTER"};
				               	if ($cluster eq $clust)
			        	       	{
							my $line = $alpsMapHash{"$unit1"}{"LINE"};
							print $fileWH "$line\n";
	                       			}
		                       		else
		                       		{
							my $line = $alpsMapHash{"$unit1"}{"LINE"};
							$line =~ s/$clust/$cluster/;
							print $fileWH "$line\n";
							#print $fileWH "$unit,,$partition\n";
		        	       		}
					} elsif (exists $alpsMapHash{"$unit0"}) {
						my $clust = $alpsMapHash{"$unit0"}{"CLUSTER"};
				               	if ($cluster eq $clust)
			        	       	{
							my $line = $alpsMapHash{"$unit0"}{"LINE"};
							print $fileWH "$line\n";
	                       			}
		                       		else
		                       		{
							my $line = $alpsMapHash{"$unit0"}{"LINE"};
							$line =~ s/$clust/$cluster/;
							print $fileWH "$line\n";
							#print $fileWH "$unit,,$partition\n";
		        	       		}
					} else {
						print $fileWH "$unit,$cluster,,Yes/No,,,\n";
					}
				}
			}
		} else {
			foreach my $partition (keys %gcHash) {
				my %unitHash = %{$gcHash{"$partition"}};
				foreach my $unit (keys %unitHash) {
					#print "UNIT $unit\n";
					my $unit1 = $unit."1";
					my $unit0 = $unit."0";
					if (exists $alpsMapHash{"$unit"}) {
	 	        	      		my $part = $alpsMapHash{"$unit"}{"PART"};
			                	if ($partition eq $part)
			                	{
							my $line = $alpsMapHash{"$unit"}{"LINE"};
							print $fileWH "$line\n";
	                        		}
	                        		else
	                	        	{
							my $line = $alpsMapHash{"$unit"}{"LINE"};
							$line =~ s/$part/$partition/;
							print $fileWH "$line\n";
							#print $fileWH "$unit,,$partition\n";
			                	}
					} elsif (exists $alpsMapHash{"$unit1"}) {
						my $part = $alpsMapHash{"$unit1"}{"PART"};
			                	if ($partition eq $part)
			                	{
							my $line = $alpsMapHash{"$unit1"}{"LINE"};
							print $fileWH "$line\n";
	                        		}
	                        		else
	                	        	{
							my $line = $alpsMapHash{"$unit1"}{"LINE"};
							$line =~ s/$part/$partition/;
							print $fileWH "$line\n";
							#print $fileWH "$unit,,$partition\n";
			                	}
					} elsif (exists $alpsMapHash{"$unit0"}) {
						my $part = $alpsMapHash{"$unit0"}{"PART"};
			                	if ($partition eq $part)
			                	{
							my $line = $alpsMapHash{"$unit0"}{"LINE"};
							print $fileWH "$line\n";
	                        		}
	                        		else
	                	        	{
							my $line = $alpsMapHash{"$unit0"}{"LINE"};
							$line =~ s/$part/$partition/;
							print $fileWH "$line\n";
							#print $fileWH "$unit,,$partition\n";
			                	}
					} else {
						print $fileWH "$unit,,$partition,Yes/No,,,\n";
					}
				}
			}
		}
		#foreach my $partition (keys %gcHash) {
		#	my %unitHash = %{$gcHash{"$partition"}};
		#	foreach my $unit (keys %unitHash) {
		#		if (exists $alpsMapHash{"$unit"}) {
	 	#              		my $part = $alpsMapHash{"$unit"}{"PART"};
		#                	if ($partition eq $part)
		#                	{
		#				my $line = $alpsMapHash{"$unit"}{"LINE"};
		#				print $fileWH "$line\n";
	        #                	}
	        #                	else
	        #                	{	
		#				print $fileWH "$unit,,$partition\n";
		#                	}
		#		} else {
		#			print $fileWH "$unit,,$partition\n";
		#		}
		#	}
		#}
	}
	else
	{
		foreach my $cluster (keys %gcHash) {
			my %partHash = %{$gcHash{"$cluster"}};
			foreach my $partition (keys %partHash) {
				my %unitHash = %{$partHash{"$partition"}};
				foreach my $unit (keys %unitHash) {
					if (exists $alpsMapHash{"$unit"}) {
	                                        my $part = $alpsMapHash{"$unit"}{"PART"};
	                                        if ($partition eq $part)
	                                        {
							my $line = $alpsMapHash{"$unit"}{"LINE"};
							print $fileWH "$line\n";
	                                        }
	                                        else
	                                        {
							print $fileWH "$unit,$cluster,$partition\n";
	                                        }
					} else {
						print $fileWH "$unit,$cluster,$partition\n";
					}
				}
			}
		}
	}
	close $fileWH;
	return 1;
}
